import streamlit as st
import requests
import json
from datetime import datetime

# Cargar la API key desde los secrets
tune_api_key = st.secrets["tune_api_key"]

# Función para realizar la solicitud a la API
def fetch_from_api(endpoint, payload):
    response = requests.post(
        f"https://proxy.tune.app/chat/{endpoint}",
        headers={
            'Authorization': tune_api_key,
            'Content-Type': 'application/json'
        },
        json=payload
    )
    if response.status_code != 200:
        raise Exception(f"Error en la respuesta del servidor: {response.status_code}")
    return response.json()

# Función para realizar la búsqueda web
def perform_web_search(query):
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "temperature": 0.7,
        "messages": [
            {
                "role": "system",
                "content": ("Eres un asistente de búsqueda web especializado en encontrar "
                            "información actualizada sobre precios de productos en Guatemala. "
                            "Proporciona un resumen conciso de los resultados más relevantes, "
                            "incluyendo fuentes confiables cuando sea posible. Formatea tu "
                            "respuesta en HTML utilizando una tabla para mostrar los resultados. "
                            "La tabla debe incluir columnas para el producto, precio, lugar y fecha. "
                            "Incluye la fecha de la búsqueda al principio de tu respuesta.")
            },
            {
                "role": "user",
                "content": (f"Realiza una búsqueda web sobre los precios actuales del siguiente "
                            f"producto en Guatemala: {query}. La fecha y hora actual en Guatemala es: {current_date}. "
                            "Muestra los resultados en una tabla HTML.")
            }
        ],
        "model": "meta/llama-3.1-405b-instruct",
        "stream": False,
        "max_tokens": 9000
    }
    data = fetch_from_api('completions', payload)
    return data['choices'][0]['message']['content']

# Interfaz de usuario en Streamlit
st.title("Precios Canasta Básica Guatemala")

st.write("Utiliza nuestra herramienta de búsqueda para encontrar información actualizada sobre los precios de los productos de la canasta básica en Guatemala.")

with st.form("product_form"):
    product_name = st.text_input("Escribe el nombre del producto (ej: arroz, frijoles, huevos):")
    submit_button = st.form_submit_button(label="Buscar")

if submit_button:
    if product_name.strip() == '':
        st.error("Por favor, ingresa el nombre de un producto antes de realizar la búsqueda.")
    else:
        with st.spinner("Realizando búsqueda web..."):
            try:
                search_results = perform_web_search(product_name)
                st.markdown(search_results, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error en la búsqueda web: {e}")

