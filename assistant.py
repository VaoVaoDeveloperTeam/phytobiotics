import json
from assistant_tools import get_structured_data_for_visualization

# Definimos la variable global para los datos históricos
historic_data = ""
# Intentamos cargar el archivo al importar el módulo
try:
    with open("research_studies.txt", "r", encoding="utf-8") as file:
        historic_data = file.read()
        print("Historical data loaded")
except FileNotFoundError:
    print("El archivo research_studies.txt no se encontró.")
except Exception as e:
    print(f"Error al leer el archivo: {e}")



def get_assistant_answer(
    client,
    user_msg:str=None,
    thread_id:str=None,
    assistant_id:str= "asst_XGCaU8czsBPqszhZzkBNxgaa" # This is BETA.
    #assistant_id:str="asst_2DXH2teVZyweB0gc1v1t4NsQ" # This is Production
    ):

    # Si la función no recibe un thread_id, genera un nuevo thread, inserta el mensaje template que se presenta al usuario en FRONT
    if not thread_id:
        print("Ningún thread_id provisto por el cliente, generando uno nuevo...")

        thread = client.beta.threads.create(
            messages=[
                {
                "role": "assistant",
                "content": "Soy un chatbot especializado en responder preguntas sobre los productos de Phytobiotics,¿en qué puedo ayudarte?",
                },
                {
                "role": "assistant",
                "content": f"Estos son los datos históricos sobre trabajos de investigación con los que cuento",#: {historic_data}",
                },
        ]) 
        thread_id=thread.id # Obtiene un nuevo thread_id y lo asigna para ser reutilizado.

        if thread_id: # checkpoint
            print(f"Nuevo thread iniciado. ID: {thread_id}")
            

    else:
        thread_id=thread_id
        print(f"El cliente proporciona thread_id y se utiliza. ID:{thread_id}")
    
    # messages.list hace un retrieve de todos los mensajes almacenados en el hilo de la conversación.
    messages = client.beta.threads.messages.list(
        thread_id=thread_id
    )
    if messages:
        print(f"El thread posee mensajes") # messages es un objeto de clase SyncCursorPage[Message]

    # Si el usuario envía por error un mensaje con una cadena vacía en su mensaje inicial, el agente se presentará con más detalle.
    if (not user_msg or user_msg == '') and len(messages)==1:  # len(messages) == 1 especifa que es el mensaje inical del thread.
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=f"Hola, me explicarías de qué forma puedes ayudarme?"
            )
        print(f"El usuario envía mensaje inicial vacío. Se agrega uno por default")

    # Si el usuario envía por error un mensaje con una cadena vacía en un mensaje NO inicial, el agente recibirá el mensaje vacío.
    elif not user_msg and len(messages)>2:
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=f""
            )
        print(f"El usuario envía mensaje vacío.")
    
    # Si el usuario envía efectivamente un mensaje con contenido, ese mensaje se agrega al hilo.
    else:
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
                role="user",
                content=user_msg
                )
        # Se obtiene un id del mensaje para identificarlo
        message_id=message.id
        print(f"Mensaje del usuario: '{user_msg}' agregado al thread.")


    ### INICIO DE LA CORRIDA DEL ASISTENTE ###
    # Una vez que el mensaje fue insertado en el hilo conversacional, correr el asistente.
    # Se envía el thread_id al assistant_id; el thread ya contiene el nuevo mensaje. El asistente recibe la conversación completa.
    if message_id and assistant_id:
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=assistant_id,
            )
        print(f"Se inicia Assistant Run...")
    
    else:
        print("No se encuentra mensaje y/o asistente para realizar una corrida")

    tool_outputs = []
    tool_output_details = {}


    if run.status == 'requires_action':
        print(f"Assistant Run requiere acciones por parte del servidor.")


        for tool_call in run.required_action.submit_tool_outputs.tool_calls:
            if tool_call.type == 'function':

                function_name = tool_call.function.name
                function_arguments = json.loads(tool_call.function.arguments)
                print(f"Tool called: function '{function_name}'")

                if function_name=='get_structured_data_for_visualization':
                    output = get_structured_data_for_visualization(function_arguments)
                    if output:
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": f"{str(output)}"
                        })
                    tool_output_details[function_name] = output

        print(f"Tools call end.")
        print(f"{tool_outputs}")

        # Submit all tool outputs at once after collecting them in a list
        if tool_outputs:
            try:
                run = client.beta.threads.runs.submit_tool_outputs_and_poll(
                    thread_id=thread_id,
                    run_id=run.id,
                    tool_outputs=tool_outputs # Se agrega el resultado de la llamada a funciones al run.
                    )
                print("Tool outputs submitted successfully.")
            except Exception as e:
                print("Failed to submit tool outputs:", e)
        else:
            print("No tool outputs to submit.")


        ###
        # el usuario solicita un gráfico 
        # envía una descripción coloquial de aquello que debe estructurarse al sub-assistant
        # el sub-assistant devuelve el objeto VizModel --> tipo de gráfico, datos del gráfico
        # el mensaje del sub assistant se acopla a tool output details
        # el asistente principal hace una explicación coloquial del gráfico
        # si la clave tool_output_details tiene contenido, usarlo
        # rescatar viz_type para decidir la función
        ### (el bloque de gráfico siempre espera) --> show viz

    if run.status == 'completed':
        print(f"Assistant Run finalizado.")

        # Una vez agregado el mensaje, se actualza la lista de mensajes y se captura el anteúltimo
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        answer = messages.data[0].content[0].text.value

        # tool_output_details es data[1]

        print(f"Respuesta: {answer}")
        print(f"Tool details: {tool_output_details}")

        return {
            "thread_id":thread_id,
            "assistant_answer_text":answer,
            "tool_output_details": tool_output_details  # En caso de no haber funciones llamadas, se devuelve el diccionario vacío.
            }