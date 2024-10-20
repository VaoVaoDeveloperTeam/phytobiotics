import json

def get_assistant_answer(
    user_msg:str=None,
    thread_id:str=None,
    assistant_id:str= "asst_B9N05bfXjNoixlFjLGnqIYL3", # Por default, el asistente organizador. 
):

    from openai import OpenAI
    client = OpenAI(api_key="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") 

    # Si la función no recibe un thread_id, genera un nuevo thread, inserta el mensaje template que se presenta al usuario en FRONT
    if not thread_id:
        print("Ningún thread_id provisto por el cliente, generando uno nuevo...")

        thread = client.beta.threads.create(
            messages=[
                {
                "role": "assistant",
                "content": f"Hola! Estoy acá para darte una mano con tu rap. ¿Cómo puedo ayudarte?"
                },
        ]) 
        thread_id=thread.id # Obtiene un nuevo thread_id y lo asigna para ser reutilizado.

        if thread_id: # checkpoint
            print(f"Nuevo thread iniciado. ID: {thread_id}")
            

    else:
        thread_id=thread_id
        print(f"El cliente proporciona thread_id, se utiliza. ID:{thread_id}")
    
    # messages.list hace un retrieve de todos los mensajes almacenados en el hilo de la conversación.
    messages = client.beta.threads.messages.list(
        thread_id=thread_id
    )
    if messages:
        print(f"El thread posee mensajes") # messages es un objeto de clase SyncCursorPage[Message]

    # Si el usuario envía por error un mensaje con una cadena vacía en su mensaje inicial, el agente se presentará con más detalle.
    if (not user_msg or user_msg == '') and len(messages)==1:
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=f"Hola amigo,me explicarías de qué forma podés ayudarme?"
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
        print("No se encuentra mensaje y/o asisnte para realizar una corrida")

    # Se inicializa una lista vacía para capturar los textos que salen de las funciones.
    tool_outputs = []

    # Se inicializa un diccionario vacío para capturar la salida estructurada de la llamada de las funciones.
    tool_output_details = {}

    # Se inicia una variable para manejar el siguiente flujo: si se llama a otro asisitente del cual se quiere obtener respuesta. usar esa respuesta textual.
    textual_answer_need = False

    if run.status == 'requires_action':
        print(f"Assistant Run requiere acciones por parte del servidor.")

        # tool_calls es una lista de las funciones llamadas por el asistente
        for tool_call in run.required_action.submit_tool_outputs.tool_calls:


            if tool_call.type == 'function':
                
                function_name = tool_call.function.name
                function_arguments = json.loads(tool_call.function.arguments)

                print(f"Tool called: function{function_name}")

                ### GET RYHMES ###
                if function_name=='get_ryhmes':
                    lyric = function_arguments.get("lyric")
                    rhyme_type = function_arguments.get("rhyme_type")
                    #ryhmes_result = get_rhymes(rap=lyric,type=rhyme_type)
                    # Al asistente se le enviaría una lista de diccionarios, cada uno con el id de la llamada, y su resultado
                    output_str = str(ryhmes_result[1])
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": output_str
                    })
                    # Al FRONT se le enviará un diccionario con los detalles del texto proviso al asistente.
                    output_details = ryhmes_result[0]
                    tool_output_details['rhymes']=output_details
                    print(f"La función {function_name} fue ejecutada exitosamente")

                
                ### GET MULETILLAS ###
                if function_name == 'get_muletillas':
                    lyric = function_arguments.get("lyric")
                    #muletillas_result = get_muletillas_list(text=lyric)
                    output_str = str(muletillas_result[0])
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": output_str
                    })
                    output_details = muletillas_result[1]
                    tool_output_details['muletillas'] = output_details
                    print(f"La función {function_name} fue ejecutada exitosamente")


                
                ### En aquellos casos en los que el asistente llama a otros asistente, imprimiremos en el front el mensaje del asistente consultado
                ### Para eso, se agrega la variable textual_answer_need --> cuando es True, se imprime en FRONT no el último mensaje (el del asistente coordinador),
                ### Sino que se imprime el del asistente consultado.

                ### GET MASTER ASSESSMENT ### 
                if function_name=='get_master_assessment':
                    textual_answer_need = True  
                    sub_assisant_called = 'Maestro Rapero'
                    lyric = function_arguments.get("lyric")
                    #textual_answer = get_master_assessment(lyric)
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": textual_answer
                    })
                    print(f"La función {function_name} fue ejecutada exitosamente")

                ### GET WOSAI ASSESSMENT ### 
                if function_name=='get_wosai_assessment':
                    textual_answer_need = True
                    sub_assisant_called = 'WosAI'
                    lyric = function_arguments.get("lyric")
                    #textual_answer = get_wosai_assessment(lyric)
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": textual_answer
                    })
                    print(f"La función {function_name} fue ejecutada exitosamente")



        print(f"Finaliza llamado a las funciones.")
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


    if run.status == 'completed':

        print(f"Assistant Run finalizado.")

        # Una vez agregado el mensaje, se actualza la lista de mensajes y se captura el anteúltimo
        messages = client.beta.threads.messages.list(thread_id=thread_id)

        # Si se llamó un sub-asistente, imprimir el mensaje textual de éste, no del coordinador.
        if textual_answer_need==True:
            # Agrego textualmente, el mensaje del sub asistente (el consultado) al hilo de la conversación
            message = client.beta.threads.messages.create(
                thread_id=thread_id,
                role="assistant",
                content= textual_answer
                )
            print(f"Se agrega el mensaje del sub-asistente {sub_assisant_called} al hilo")
            # Aviso que el mensaje a rescatar es el último agregado. 
            message_index = 0
        else:
            # El del asistente que hizo la corrida queda como ante - último
            message_index = 0

        answer = messages.data[message_index].content[0].text.value

        print(f"Respuesta: {answer}")

        return {
            "thread_id":thread_id,
            "assistant_answer_text":answer,
            "tool_output_details": tool_output_details  # En caso de no haber funciones llamadas, se devuelve el diccionario vacío.
            }