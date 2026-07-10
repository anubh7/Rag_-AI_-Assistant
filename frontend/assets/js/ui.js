// General UI orchestration:
// loading collections and connecting frontend modules.

const UI = {


  activeCollection: "rag_documents",



  bindEvents() {

    Upload.bind();

    Chat.bind();

    this.loadCollections();

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



  }


};