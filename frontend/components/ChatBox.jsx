import React, { useState } from "react";
import Message from "./Message";


export default function ChatBox({ onSend }) {


  const [messages, setMessages] = useState([]);

  const [input, setInput] = useState("");

  const [useDocument, setUseDocument] = useState(true);



  const handleSend = async () => {


    if (!input.trim())
      return;


    const userMessage = {
      role: "user",
      content: input
    };


    setMessages(prev => [
      ...prev,
      userMessage
    ]);


    const question = input;


    setInput("");



    try {


      const result = await onSend(
        question,
        useDocument
      );



      let answer;


      if (result.status === "success") {

        answer = result.data.answer;

      }

      else {

        answer = "Error : " + result.message;

      }



      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          content: answer
        }
      ]);


    }

    catch (error) {


      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          content: "Backend error"
        }
      ]);


    }



  };



  return (

    <div className="chat-container">


      <div className="messages">


        {
          messages.map((msg, index) => (

            <Message

              key={index}

              role={msg.role}

              content={msg.content}

            />


          ))

        }


      </div>



      <div className="rag-toggle">


        <label>

          <input

            type="checkbox"

            checked={useDocument}

            onChange={
              e => setUseDocument(e.target.checked)
            }

          />


          Use uploaded documents


        </label>


      </div>




      <div className="chat-input">


        <input

          value={input}

          onChange={
            e => setInput(e.target.value)
          }


          onKeyDown={
            e => {
              if (e.key === "Enter")
                handleSend()
            }
          }


          placeholder={
            useDocument
              ?
              "Ask about your documents..."
              :
              "Ask anything..."
          }

        />



        <button onClick={handleSend}>

          Send

        </button>



      </div>



    </div>


  );


}