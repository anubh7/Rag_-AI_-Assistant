// Handles document upload

const Upload = {

  bind() {

    document
      .getElementById("upload-btn")
      .addEventListener("click", () => this.upload());

  },


  async upload() {

    const input = document.getElementById("file-input");

    const status = document.getElementById("upload-status");


    if (!input.files.length) {

      status.textContent = "Please choose a file first.";

      return;

    }


    status.textContent = "Uploading...";


    try {

      const activeCollection = UI.getActiveCollection();

      const result = await Api.uploadFile(

        input.files[0],

        activeCollection

      );


      if (result.status === "success") {

        status.textContent =
          `Indexed ${result.data.chunks_created} chunks successfully.`;

        input.value = "";

        if (typeof UI.loadCollections === "function") {

          UI.loadCollections();

        }

      }

      else {

        status.textContent =
          "Error: " + (result.message || "Upload failed. Please try a supported file format (PDF, CSV, DOCX, TXT, XLSX).");

      }

    }

    catch (error) {

      console.error(error);

      status.textContent =
        "Unable to connect to backend. Is the API server running on port 8000?";

    }

  }

};