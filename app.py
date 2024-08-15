import streamlit as st
import requests
import pandas as pd
import json
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

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
    Extrae los precios de los productos de la siguiente información:
    {resultado}
    
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
    """
    
    url = "https://api.together.xyz/inference"
    headers = {
        "Authorization": f"Bearer {together_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "togethercomputer/llama-2-70b-chat",
        "prompt": prompt,
        "max_tokens": 1000,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return json.loads(result['output']['choices'][0]['text'])
    except requests.RequestException as e:
        logging.error(f"Error al llamar a la API de Together: {e}")
        logging.error(f"Respuesta de la API: {response.text}")
        st.error(f"Error al extraer precios: {e}")
        return None

def main():
    st.title("Buscador de Precios en Guatemala")
    
    query = st.text_input("Ingrese el producto que desea buscar:")
    
    if st.button("Buscar"):
        with st.spinner("Buscando precios..."):
            resultados = buscar_productos(query)
            if resultados:
                precios = extraer_precios(resultados)
                
                if precios and 'productos' in precios:
                    df = pd.DataFrame(precios['productos'])
                    df['precio'] = pd.to_numeric(df['precio'], errors='coerce')
                    
                    st.subheader("Resultados:")
                    st.dataframe(df.sort_values('precio'))
                    
                    if not df.empty:
                        precio_min = df['precio'].min()
                        precio_max = df['precio'].max()
                        
                        st.subheader("Resumen:")
                        st.write(f"Precio más bajo: Q{precio_min:.2f}")
                        st.write(f"Precio más alto: Q{precio_max:.2f}")
                    else:
                        st.warning("No se encontraron precios para este producto.")
                else:
                    st.error("No se pudo extraer la información de precios.")

if __name__ == "__main__":
    main()
