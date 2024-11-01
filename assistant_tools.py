import streamlit as st
from openai import OpenAI
from pydantic import BaseModel
from typing import Dict, List, Union

def get_structured_data_for_visualization(
    function_arguments:dict,
    ):
    
    visualization_type = function_arguments.get("visualization_type","")
    visualization_title = function_arguments.get("visualization_title","")
    visualization_data = function_arguments.get("visualization_data","")

    print(visualization_type)
    print(visualization_title)
    print(visualization_data)

    #if not openai_client:
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    openai_client = OpenAI(api_key=openai_api_key)

    # Definimos system message
    system_message = """
    Eres un experto en estructurar texto que contiene información graficable para ser graficada.
    Tu tarea convertir texto desestructurado en un diccionario que contenga 3 elementos claves:
    1. El tipo de visualización que desea hacerse (barras, dispersión o líneas)
    2. El título que se le quiere asignar a la visualización
    3. Los datos estructurados para la visualización

    Por ejemplo, el diccionario podría verse de la siguiente manera:
    
    # Diccionario con las instrucciones de visualización
    
    viz_instructions = {
        "viz_type": "bar",
        "viz_title": "Tasa de conversión alimenticia por especie",
        'viz_data': {
            "especie": ["pollo", "gallina", "cerda"],
            'conversion': [1.5, 2.0, 1.3]
        }
    }

    Probablmente, utilice Altair para realizar los gráficos, así que el exe x y el eje y deberían ser las claves de "viz_data", y sus valores deberían estar presentados como listas.
    Por favor, mantente fiel a la información 
    """

    class VizModel(BaseModel):
        viz_type: str
        viz_title: str
        viz_data: str    


    chat_completion = openai_client.beta.chat.completions.parse(
        model='gpt-4o',
        temperature=0.1,
        seed=42,
        messages=[
            {
                "role": "system",
                "content": system_message
            },
            {
                "role": "user",
                "content": f"Genera un diccionario estructurado para rearlizar un gráfico de tipo {visualization_type}, con título '{visualization_title}', y contenga la siguiente información: '{visualization_data}'"
            }
        ],
        response_format=VizModel,
    )
    answer = chat_completion.choices[0].message.content
    print (answer)
    return eval(answer)
    #return eval(chat_completion.choices[0].message.content)
    


        