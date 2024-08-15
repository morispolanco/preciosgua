import streamlit as st
import requests
import pandas as pd
import json
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)

# Configurar las claves de API desde los secrets de Streamlit
serper_api_key = st.secrets["serper_api_key"]
together_api_key = st.secrets["together_api_key"]

def buscar_productos(query):
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": f"{query} precio Guatemala",
        "num": 20
    })
    headers = {
        'X-API-KEY': serper_api_key,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error al llamar a la API de Serper: {e}")
        st.error(f"Error al buscar productos: {e}")
        return None

def extraer_precios(resultado):
    prompt = f"""
    Extrae los precios de los productos de la siguiente información de búsqueda:
    {json.dumps(resultado, ensure_ascii=False)}
    
    Devuelve los resultados en el siguiente formato JSON:
    {{
        "productos": [
            {{
                "nombre": "Nombre del producto",
                "precio": 100.00,
                "tienda": "Nombre de la tienda"
            }}
        ]
    }}
    
    Asegúrate de incluir solo productos con precios válidos y en quetzales (Q).
    """
    
    url = "https://api.together.xyz/v1/completions"
    headers = {
        "Authorization": f"Bearer {together_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "togethercomputer/llama-2-70b-chat",
        "prompt": prompt,
        "max_tokens": 1000,
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "repetition_penalty": 1,
        "stop": ["</s>", "[/INST]"]
    }
    
    try:
        logging.debug(f"Enviando solicitud a Together API: {json.dumps(data, indent=2)}")
        response = requests.post(url, headers=headers, json=data)
        logging.debug(f"Respuesta de Together API: {response.text}")
        response.raise_for_status()
        result = response.json()
        return json.loads(result['choices'][0]['text'])
    except requests.RequestException as e:
        logging.error(f"Error al llamar a la API de Together: {e}")
        logging.error(f"Respuesta de la API: {response.text}")
        st.error(f"Error al extraer precios: {e}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Error al decodificar la respuesta JSON: {e}")
        st.error("Error al procesar la respuesta de la API")
        return None

def main():
    st.title("Buscador de Precios en Guatemala")
    
    query = st.text_input("Ingrese el producto que desea buscar:")
    
    if st.button("Buscar"):
        with st.spinner("Buscando precios..."):
            resultados_busqueda = buscar_productos(query)
            if resultados_busqueda:
                precios = extraer_precios(resultados_busqueda)
                
                if precios and 'productos' in precios:
                    df = pd.DataFrame(precios['productos'])
                    if not df.empty:
                        df['precio'] = pd.to_numeric(df['precio'], errors='coerce')
                        df = df.dropna(subset=['precio'])
                        
                        st.subheader("Resultados:")
                        st.dataframe(df.sort_values('precio'))
                        
                        if not df.empty:
                            precio_min = df['precio'].min()
                            precio_max = df['precio'].max()
                            
                            st.subheader("Resumen:")
                            st.write(f"Precio más bajo: Q{precio_min:.2f}")
                            st.write(f"Precio más alto: Q{precio_max:.2f}")
                        else:
                            st.warning("No se encontraron precios válidos para este producto.")
                    else:
                        st.warning("No se encontraron productos con precios válidos.")
                else:
                    st.error("No se pudo extraer la información de precios.")
            else:
                st.error("No se pudieron obtener resultados de búsqueda.")

if __name__ == "__main__":
    main()
