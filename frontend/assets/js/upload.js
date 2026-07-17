// Handles document upload — supports single or multiple files at once.

const Upload = {

  bind() {
    document
      .getElementById("upload-btn")
      .addEventListener("click", () => this.upload());

    // Live file count feedback when user selects files
    document
      .getElementById("file-input")
      .addEventListener("change", () => this.onFileChange());
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

      if (result.status === "success") {
        const d = result.data;

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
        input.value = "";

        // Refresh collection list
        if (typeof UI.loadCollections === "function") {
          UI.loadCollections();
        }

      } else {
        status.textContent = "Error: " + (result.message || "Upload failed. Check file formats (PDF, CSV, DOCX, TXT, XLSX).");
        status.style.color = "#ef4444";
      }

    } catch (error) {
      console.error(error);
      status.textContent = "Unable to connect to backend. Is the API server running on port 8000?";
      status.style.color = "#ef4444";
    }

  }

};