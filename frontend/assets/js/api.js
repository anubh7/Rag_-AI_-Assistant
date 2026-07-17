const API_BASE = "http://localhost:8000";


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


