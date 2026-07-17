// General UI orchestration:
// loading collections and connecting frontend modules.

const UI = {


  activeCollection: "rag_documents",



  bindEvents() {

    Upload.bind();

    Chat.bind();


    // Update user profile displays
    const username = Auth.getUsername();
    const role = Auth.getRole();
    document.getElementById("user-display").textContent = `${username} (${role})`;

    // Bind logout and session reset listeners
    document.getElementById("logout-btn").addEventListener("click", () => Auth.logout());
    document.getElementById("new-chat-btn").addEventListener("click", () => Chat.newSession());

    this.loadCollections();
    this.loadSessions();

  },




  getActiveCollection() {

    return this.activeCollection;

  },





  async loadCollections() {


    try {


      const result = await Api.listCollections();


      const list =
        document.getElementById("collection-list");



      list.innerHTML = "";



      if (result.status !== "success") {

        return;

      }




      result.data.forEach((name) => {



        const li =
          document.createElement("li");



        li.textContent = name;




        li.addEventListener("click", () => {


          this.activeCollection = name;



          document

            .querySelectorAll("#collection-list li")

            .forEach((el) => {

              el.classList.remove("active");

            });



          li.classList.add("active");



        });



        list.appendChild(li);



      });



      // Automatically select first collection

      if (result.data.length > 0) {


        this.activeCollection = result.data[0];


        document
          .querySelector("#collection-list li")
          ?.classList.add("active");


      }



    }

    catch (error) {


      console.error(
        "Collection loading error:",
        error
      );


    }



  },

  async loadSessions() {
    const list = document.getElementById("session-list");
    list.innerHTML = "<li style='cursor:default; background:transparent; font-size:12px; color:#64748b;'>Loading history...</li>";
    try {
      const result = await Api.listSessions();
      list.innerHTML = "";
      if (result.status !== "success" || !result.data || result.data.length === 0) {
        list.innerHTML = "<li style='cursor:default; background:transparent; font-size:12px; color:#64748b;'>No sessions recorded</li>";
        return;
      }
      result.data.forEach((session) => {
        const li = document.createElement("li");
        li.setAttribute("data-id", session.id);
        if (Chat.sessionId === session.id) {
          li.classList.add("active");
        }

        const textSpan = document.createElement("span");
        textSpan.className = "session-item-text";
        textSpan.textContent = session.title || "Chat Session";
        
        // Load session on clicking title
        textSpan.addEventListener("click", () => {
          document.querySelectorAll("#session-list li").forEach(el => el.classList.remove("active"));
          li.classList.add("active");
          Chat.loadSession(session.id);
        });

        // Delete button
        const deleteBtn = document.createElement("button");
        deleteBtn.className = "session-delete-btn";
        deleteBtn.innerHTML = "&times;";
        deleteBtn.title = "Delete session";
        deleteBtn.addEventListener("click", async (e) => {
          e.stopPropagation();
          if (confirm(`Delete chat session "${session.title}"?`)) {
            const deleteResult = await Api.deleteSession(session.id);
            if (deleteResult.status === "success") {
              if (Chat.sessionId === session.id) {
                Chat.newSession();
              }
              this.loadSessions();
            } else {
              alert("Failed to delete chat session: " + deleteResult.message);
            }
          }
        });

        li.appendChild(textSpan);
        li.appendChild(deleteBtn);
        list.appendChild(li);
      });
    } catch (error) {
      console.error("Failed to load sessions:", error);
      list.innerHTML = "<li style='cursor:default; background:transparent; font-size:12px; color:#f87171;'>Error loading sessions</li>";
    }
  }


};