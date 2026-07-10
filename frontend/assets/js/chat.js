// Handles chat send/receive and rendering messages.

const Chat = {

  sessionId: "session-" + Date.now(),


  bind() {

    document
      .getElementById("send-btn")
      .addEventListener("click", () => this.send());


    document
      .getElementById("chat-input")
      .addEventListener("keydown", (e) => {

        if (e.key === "Enter") {
          this.send();
        }

      });

  },



  async send() {


    const input = document.getElementById("chat-input");


    const query = input.value.trim();


    if (!query) return;



    // Show user message

    this.renderMessage(
      "user",
      query
    );


    input.value = "";



    // Get selected collection

    const activeCollection = UI.getActiveCollection();



    // Get RAG toggle value

    const useDocument =
      document.getElementById("rag-toggle").checked;



    // Call backend
    try {

      const result = await Api.sendChat(

        query,

        this.sessionId,

        activeCollection,

        useDocument

      );




      if (result.status === "success") {


        this.renderMessage(

          "assistant",

          result.data.answer

        );


      }

      else {


        this.renderMessage(

          "assistant",

          `Error: ${result.message}`

        );


      }

    } catch (error) {

      console.error("Chat error:", error);

      this.renderMessage(
        "assistant",
        `⚠️ Could not reach the backend. Make sure the FastAPI server is running at http://localhost:8000. (${error.message})`
      );

    }



  },




  renderMessage(role, text) {


    const container =
      document.getElementById("messages");



    const bubble =
      document.createElement("div");



    bubble.className =
      `message ${role}`;



    bubble.textContent =
      text;



    container.appendChild(
      bubble
    );



    container.scrollTop =
      container.scrollHeight;


  },


};