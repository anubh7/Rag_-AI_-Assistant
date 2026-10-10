// Handles document upload — supports single or multiple files at once.

const Upload = {

  /** job_id of the upload currently running in the background, or null. */
  activeJobId: null,

  bind() {
    document
      .getElementById("upload-btn")
      .addEventListener("click", () => this.upload());

    // Live file count feedback when user selects files
    document
      .getElementById("file-input")
      .addEventListener("change", () => this.onFileChange());

    const cancelBtn = document.getElementById("cancel-upload-btn");
    if (cancelBtn) {
      cancelBtn.addEventListener("click", () => this.cancel());
    }
  },


  /**
   * Ask the backend to stop the job that is currently being polled.
   * We optimistically disable the button; the next poll observes the
   * 'cancelled' status and renders the final message.
   */
  async cancel() {

    if (!this.activeJobId) return;

    const btn = document.getElementById("cancel-upload-btn");
    if (btn) {
      btn.disabled = true;
      btn.textContent = "Cancelling…";
    }

    try {
      await Api.cancelUploadJob(this.activeJobId);
    } catch (error) {
      console.error(error);
      // The poll loop will still notice the cancel server-side; only re-enable
      // if the request itself failed to reach the server.
      if (btn) {
        btn.disabled = false;
        btn.textContent = "Cancel";
      }
    }
  },


  /** Shows the Cancel button and remembers which job it aborts. */
  showCancel(jobId) {
    this.activeJobId = jobId;
    const btn = document.getElementById("cancel-upload-btn");
    if (btn) {
      btn.hidden = false;
      btn.disabled = false;
      btn.textContent = "Cancel";
    }
  },


  /** Hides the Cancel button and forgets the job. */
  hideCancel() {
    this.activeJobId = null;
    const btn = document.getElementById("cancel-upload-btn");
    if (btn) {
      btn.hidden = true;
      btn.disabled = false;
      btn.textContent = "Cancel";
    }
  },


  onFileChange() {
    const input  = document.getElementById("file-input");
    const status = document.getElementById("upload-status");
    const count  = input.files.length;

    if (count === 0) {
      status.textContent = "";
    } else if (count === 1) {
      status.textContent = `📄 1 file selected: ${input.files[0].name}`;
    } else {
      const names = Array.from(input.files).map(f => f.name).join(", ");
      status.textContent = `📄 ${count} files selected: ${names}`;
    }

    status.style.color = "#6b7280";
  },


  async upload() {

    const input  = document.getElementById("file-input");
    const status = document.getElementById("upload-status");

    if (!input.files.length) {
      status.textContent = "Please choose at least one file first.";
      status.style.color = "#ef4444";
      return;
    }

    const count = input.files.length;
    status.innerHTML = `⏳ Uploading ${count} file${count > 1 ? "s" : ""}…`;
    status.style.color = "#6b7280";

    try {

      const activeCollection = UI.getActiveCollection();

      // Send ALL selected files in a single request
      const result = await Api.uploadFiles(input.files, activeCollection);

      // New backend flow: accepted files are processed by a background job.
      // Poll the job for live stage/progress instead of holding the request open.
      if (result.status === "success" && result.data && result.data.job_id) {
        await this.pollJob(result.data, status, input);
        return;
      }

      if (result.status === "success") {
        // Legacy synchronous response shape (kept as a fallback).
        this.renderResult(result.data, status, input);

      } else {
        let msg = "Error: " + (result.message || "Upload failed. Check file formats (PDF, CSV, DOCX, TXT, XLSX).");
        // Surface per-file backend errors (e.g. scanned PDF with no extractable text)
        if (result.data && result.data.errors && result.data.errors.length > 0) {
          msg += "\n" + result.data.errors.map(e => `• ${e.file}: ${e.error}`).join("\n");
        }
        status.textContent = msg;
        status.style.color = "#ef4444";
        status.style.whiteSpace = "pre-line";
      }

    } catch (error) {
      console.error(error);
      status.textContent = "Unable to connect to backend. Is the API server running on port 8001?";
      status.style.color = "#ef4444";
    }

  },


  /**
   * Renders the final summary for an upload (used by both the job flow and
   * the legacy synchronous response shape).
   * d = { uploaded, errors, total_files_processed, total_files_failed,
   *       total_pages_loaded, total_chunks_created }
   */
  renderResult(d, status, input) {

    // Build a per-file result list
    let html = `<strong style="color:#10b981">✔ ${d.total_files_processed} file(s) indexed</strong><br>`;
    html += `<span style="font-size:11px;color:#6b7280">${d.total_chunks_created} chunks · ${d.total_pages_loaded} pages loaded</span>`;

    // Show individual success rows
    if (d.uploaded && d.uploaded.length > 0) {
      html += `<ul style="margin:6px 0 0;padding-left:14px;font-size:11px;color:#374151">`;
      d.uploaded.forEach(r => {
        html += `<li>✅ <b>${r.file}</b> — ${r.chunks_created} chunks</li>`;
      });
      html += `</ul>`;
    }

    // Show failed files if any
    if (d.errors && d.errors.length > 0) {
      html += `<ul style="margin:4px 0 0;padding-left:14px;font-size:11px;color:#dc2626">`;
      d.errors.forEach(e => {
        html += `<li>❌ <b>${e.file}</b> — ${e.error}</li>`;
      });
      html += `</ul>`;
    }

    status.innerHTML = html;
    status.style.color = "";
    status.style.whiteSpace = "";
    input.value = "";

    // Refresh collection list
    if (typeof UI.loadCollections === "function") {
      UI.loadCollections();
    }
  },


  /**
   * Polls GET /upload/jobs/{id} until the background job finishes,
   * showing live stage/progress (pages loaded, chunks embedded, % done).
   * @param {object} accepted - the initial POST /upload/ data (job_id, errors)
   */
  async pollJob(accepted, status, input) {

    const jobId = accepted.job_id;
    const maxAttempts = 1800;      // ~45 minutes at 1.5 s per poll
    const pollIntervalMs = 1500;
    let lastLine = "";

    // The job is accepted and will run in the background, so the Cancel button
    // must be shown now — otherwise it stays `hidden` for the whole run.
    this.showCancel(jobId);

    for (let attempt = 0; attempt < maxAttempts; attempt++) {

      await new Promise(resolve => setTimeout(resolve, pollIntervalMs));

      let res;
      try {
        res = await Api.getUploadJob(jobId);
      } catch (e) {
        continue;   // transient network hiccup — keep polling
      }

      const job = (res && res.data && res.data.job_id) ? res.data : null;

      if (!job) {
        // No job payload: session expired or job vanished from memory.
        if (res && res.status === "error") {
          status.textContent = res.message || "Lost contact with the server.";
          status.style.color = "#ef4444";
          return;
        }
        continue;
      }

      if (job.status === "queued" || job.status === "running") {

        const pct = job.chunks_total > 0
          ? ` — ${Math.round((job.chunks_indexed / job.chunks_total) * 100)}%`
          : "";

        const line = `⏳ ${job.message || "Processing…"}${pct}`;

        if (line !== lastLine) {
          let html = `<span style="color:#6b7280">${line}</span>`;
          html += `<br><span style="font-size:11px;color:#9ca3af">`
                + `${job.files_done}/${job.total_files} file(s) · `
                + `${job.pages_loaded} page(s) loaded · `
                + `${job.chunks_indexed}/${job.chunks_total || "?"} chunks embedded`
                + `</span>`;
          status.innerHTML = html;
          lastLine = line;
        }
        continue;
      }

      if (job.status === "completed") {

        // Merge errors reported when the job was accepted (bad extensions etc.)
        // with errors collected while processing.
        const d = job.result || {};
        const preErrors = accepted.errors || [];
        if (preErrors.length > 0) {
          d.errors = [...preErrors, ...(d.errors || [])];
          d.total_files_failed = (d.total_files_failed || 0) + preErrors.length;
        }
        this.hideCancel();
        this.renderResult(d, status, input);
        return;
      }

      if (job.status === "failed") {

        this.hideCancel();
        const errs = [
          ...(accepted.errors || []),
          ...((job.result && job.result.errors) || []),
        ];
        let msg = "Error: " + (job.error || "Upload failed.");
        if (errs.length > 0) {
          msg += "\n" + errs.map(e => `• ${e.file}: ${e.error}`).join("\n");
        }
        status.textContent = msg;
        status.style.color = "#ef4444";
        status.style.whiteSpace = "pre-line";
        input.value = "";
        return;
      }

      if (job.status === "cancelled") {

        // Cooperative cancel: whatever was embedded before the cancel is still
        // in the collection and searchable, so report it rather than failing.
        this.hideCancel();
        status.textContent = job.message ||
          "Upload cancelled. Any chunks already indexed remain searchable.";
        status.style.color = "#f59e0b";
        status.style.whiteSpace = "pre-line";
        input.value = "";
        if (typeof UI.loadCollections === "function") {
          UI.loadCollections();
        }
        return;
      }
    }

    this.hideCancel();
    status.textContent = "Upload is taking longer than expected — it may still be running; check the backend logs.";
    status.style.color = "#ef4444";
  }

};
