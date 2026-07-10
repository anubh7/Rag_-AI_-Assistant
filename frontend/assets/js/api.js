const API_BASE = "http://localhost:8000";


const Api = {


  async uploadFile(file, collectionName = "rag_documents") {


    const formData = new FormData();

    formData.append("file", file);
    formData.append("collection_name", collectionName);



    const response = await fetch(
      `${API_BASE}/upload/`,
      {
        method: "POST",
        body: formData
      }
    );


    return await response.json();


  },



  async sendChat(query, sessionId, collectionName, useDocument = true) {


    const response = await fetch(

      `${API_BASE}/chat/`,

      {

        method: "POST",

        headers: {
          "Content-Type": "application/json"
        },


        body: JSON.stringify({

          query: query,

          session_id: sessionId,

          collection_name: collectionName,

          use_rag: useDocument


        })


      }

    );


    return await response.json();


  },


  async listCollections() {

    const response = await fetch(`${API_BASE}/collection/`);

    return await response.json();

  }



};

