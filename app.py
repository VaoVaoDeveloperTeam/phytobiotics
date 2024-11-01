import streamlit as st
from openai import OpenAI
import os
import json
from dotenv import load_dotenv
from assistant import get_assistant_answer

openai_api_key = st.secrets["OPENAI_API_KEY"]

# Initialize OpenAI API client
if openai_api_key:
    openai_client = OpenAI(api_key=openai_api_key)
    if openai_client:
        print("OpenAI client created.")
else:
    st.error("Failed to load OpenAI API key")
    st.stop()  # Stop execution if the key is not found


# Initialize the Streamlit app
def main():
    st.set_page_config(page_title="Your Chat App", page_icon=":speech_balloon:")

    # Show title and description.
    st.title("📄 AI Phytobiotics Assistant:")
    st.write(
        "ChatBot especializado en responder preguntas sobre los productos de Phytobiotics"
    )

    # Authentication
    proceed = False
    password = st.text_input("App Password", type="password")

    if not password:
        st.info("Por favor, ingrese la clave de la aplicación.", icon="🗝️")
    else:
        if password != st.secrets["app_password"]:
            st.info("La clave provista es incorrecta.", icon="🗝️")
        else: 
            proceed = True
    #################
    proceed = True
    #################
    if proceed == True:
        # Verificamos si 'thread_id' está en session_state, si no, lo inicializamos
        if "thread_id" not in st.session_state:
            st.session_state.thread_id = None

        # Inicializamos el historial de mensajes si no está en session_state
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Mensaje inicial del asistente
        if len(st.session_state.messages) == 0:
            initial_message = "Hola, ¿en qué puedo ayudarte hoy en relación a los estudios de Phytobiotics?"
            st.session_state.messages.append({"role": "assistant", "content": initial_message})

        # Muestra los mensajes en la conversación
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Input del usuario
        user_input = st.chat_input("Escribe tu mensaje aquí...")

        # Cuando el usuario envía un mensaje
        if user_input:

            # Añade el mensaje del usuario a la sesión
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            # Envía el mensaje al modelo de OpenAI y solicita la respuesta (get_assistant_answer)
            assistant_response = get_assistant_answer(openai_client, user_input, st.session_state.thread_id)
            answer = assistant_response["assistant_answer_text"]

            st.session_state.thread_id = assistant_response["thread_id"]  # Actualizamos el thread_id
            print(f"thread id de la conversación actual: {st.session_state.thread_id}")

            # Añade la respuesta del asistente a la sesión
            st.session_state.messages.append({"role": "assistant", "content": answer})
            with st.chat_message("assistant"):
                st.markdown(answer)

            # Check if there is structured data for visualization
            assistant_response_details = assistant_response["tool_output_details"]
            print(f"Tool output details FRONT received: {assistant_response_details}")

            if "get_structured_data_for_visualization" in assistant_response_details:
                
                print("Details provided are for visualization")
                
                viz_instructions = assistant_response_details["get_structured_data_for_visualization"]
                print(f"Viz instructions:{viz_instructions}")

                viz_type = viz_instructions["viz_type"]
                viz_title = viz_instructions["viz_title"]
                viz_data = json.loads(viz_instructions["viz_data"])
                print(f"{viz_data}")

                first_key = list(viz_data.keys())[0]
                second_key = list(viz_data.keys())[1]

                print(f"First key: {first_key}, Second key: {second_key}")
                st.write(viz_title)
                if viz_type == "bar":
                    st.bar_chart(viz_data, x=first_key, y=second_key,horizontal=True)                        


# Run the Streamlit app
if __name__ == '__main__':
    main()