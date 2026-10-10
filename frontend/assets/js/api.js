const API_BASE = "http://localhost:8001";


const Api = {

  async handleResponse(response) {
    if (response.status === 401) {
      Auth.logout();
      return { status: "error", message: "Unauthorized. Session expired." };
    }
    return await response.json();
  },


  /**
   * Upload one or more files to the backend.
   * @param {FileList|File[]} files - Files selected by the user
   * @param {string} collectionName - Qdrant collection to index into
   */
  async uploadFiles(files, collectionName = "rag_documents") {
    const formData = new FormData();

    // Append every file under the same key — FastAPI receives List[UploadFile]
    Array.from(files).forEach(file => {
      formData.append("files", file);
    });

    formData.append("collection_name", collectionName);

    const response = await fetch(
      `${API_BASE}/upload/`,
      {
        method: "POST",
        headers: Auth.getAuthHeaders(),
        body: formData
      }
    );

    return await this.handleResponse(response);
  },


  /**
   * Poll a background upload job started by uploadFiles().
   * @param {string} jobId - job_id returned in the upload response
   * @returns {Promise<object>} { status, message, data: { status, stage, message, chunks_indexed, ... } }
   */
  async getUploadJob(jobId) {
    const response = await fetch(
      `${API_BASE}/upload/jobs/${jobId}`,
      {
        headers: Auth.getAuthHeaders()
      }
    );
    return await this.handleResponse(response);
  },


  /**
   * Ask a running background upload job to stop.
   *
   * Cancellation is cooperative — the worker checks the flag between parsed
   * pages and between embedding batches, so it stops within one batch rather
   * than running the whole file to completion. Chunks already indexed stay in
   * the collection and remain searchable; only the remaining work is dropped.
   *
   * @param {string} jobId - job_id returned by uploadFiles()
   * @returns {Promise<object>} { status:"success", message, data:{ job_id, status } }
   */
  async cancelUploadJob(jobId) {
    const response = await fetch(
      `${API_BASE}/upload/jobs/${jobId}/cancel`,
      {
        method: "POST",
        headers: Auth.getAuthHeaders()
      }
    );
    return await this.handleResponse(response);
  },


  async sendChat(query, sessionId, collectionName, useDocument = true, filters = null) {
    const body = {
      query: query,
      session_id: sessionId,
      collection_name: collectionName,
      use_rag: useDocument,
    };

    // Only include filters in the payload when the user has defined at least one
    if (filters && (
      (filters.must && filters.must.length > 0) ||
      (filters.must_not && filters.must_not.length > 0) ||
      (filters.should && filters.should.length > 0)
    )) {
      body.filters = filters;
    }

    const response = await fetch(
      `${API_BASE}/chat/`,
      {
        method: "POST",
        headers: Auth.getAuthHeaders({
          "Content-Type": "application/json"
        }),
        body: JSON.stringify(body)
      }
    );

    return await this.handleResponse(response);
  },


  /**
   * Stream a chat response over SSE (POST /chat/stream).
   *
   * Tokens are delivered to `handlers.onToken(text, fullAnswer)` as the model
   * generates them, so the UI can render progressively instead of waiting for
   * the whole answer. Resolves with the same shape as sendChat():
   *   { status:"success", data:{ answer, sources, session_id } }
   *
   * @param {object} handlers - optional { onToken, onSources, onRag, onDone }
   */
  async sendChatStream(query, sessionId, collectionName, useDocument = true, filters = null, handlers = {}) {
    const body = {
      query: query,
      session_id: sessionId,
      collection_name: collectionName,
      use_rag: useDocument,
    };

    if (filters && (
      (filters.must && filters.must.length > 0) ||
      (filters.must_not && filters.must_not.length > 0) ||
      (filters.should && filters.should.length > 0)
    )) {
      body.filters = filters;
    }

    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: "POST",
      headers: Auth.getAuthHeaders({
        "Content-Type": "application/json"
      }),
      body: JSON.stringify(body)
    });

    if (response.status === 401) {
      Auth.logout();
      return { status: "error", message: "Unauthorized. Session expired." };
    }
    if (!response.ok || !response.body) {
      throw new Error(`Streaming chat failed (HTTP ${response.status})`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let buffer = "";
    let answer = "";
    let sources = [];
    let streamError = null;

    const handleEvent = (event) => {
      if (event.type === "token") {
        answer += event.text || "";
        if (handlers.onToken) handlers.onToken(event.text || "", answer);
      } else if (event.type === "sources") {
        sources = event.sources || [];
        if (handlers.onSources) handlers.onSources(sources);
      } else if (event.type === "start") {
        if (handlers.onRag) handlers.onRag(!!event.rag);
      } else if (event.type === "done") {
        if (event.answer) answer = event.answer;   // final PII-masked answer
        if (handlers.onDone) handlers.onDone(answer);
      } else if (event.type === "error") {
        streamError = event.message || "Generation failed.";
      }
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split("\n");
      buffer = lines.pop();   // keep the (possibly partial) last line in the buffer

      for (const line of lines) {
        if (!line.startsWith("data:")) continue;
        const raw = line.slice(5).trim();
        if (!raw) continue;
        try {
          handleEvent(JSON.parse(raw));
        } catch (e) {
          console.warn("Skipping malformed SSE line:", raw, e);
        }
      }
    }

    if (streamError) {
      if (answer) {
        // Partial answer — return it so the user keeps what was generated.
        return {
          status: "success",
          data: { answer, sources, session_id: sessionId, warning: streamError }
        };
      }
      return { status: "error", message: streamError };
    }

    return { status: "success", data: { answer, sources, session_id: sessionId } };
  },


  async listCollections() {
    const response = await fetch(
      `${API_BASE}/collection/`,
      {
        headers: Auth.getAuthHeaders()
      }
    );
    return await this.handleResponse(response);
  },

  async listSessions() {
    const response = await fetch(
      `${API_BASE}/chat/sessions`,
      {
        headers: Auth.getAuthHeaders()
      }
    );
    return await this.handleResponse(response);
  },

  async getSessionMessages(sessionId) {
    const response = await fetch(
      `${API_BASE}/chat/sessions/${sessionId}`,
      {
        headers: Auth.getAuthHeaders()
      }
    );
    return await this.handleResponse(response);
  },

  async deleteSession(sessionId) {
    const response = await fetch(
      `${API_BASE}/chat/sessions/${sessionId}`,
      {
        method: "DELETE",
        headers: Auth.getAuthHeaders()
      }
    );
    return await this.handleResponse(response);
  }

};


