import streamlit as st
import requests
import json

# Cargar las API keys desde los secrets
serper_api_key = st.secrets["serper_api_key"]
together_api_key = st.secrets["together_api_key"]

# Función para obtener precios usando la API de Serper
def get_prices(product_name):
    headers = {
        "X-API-KEY": serper_api_key,
        "Content-Type": "application/json"
    }
    query = {
        "q": f"{product_name} price Guatemala"
    }
    response = requests.post("https://api.serper.dev/search", headers=headers, json=query)
    results = response.json()
    
    # Suponiendo que los precios se encuentran en el campo 'prices' del resultado
    prices = results.get("prices", [])
    return prices

# Función para generar la descripción con Together
def generate_description(product_name, prices):
    headers = {
        "Authorization": f"Bearer {together_api_key}",
        "Content-Type": "application/json"
    }
    prompt = f"Provide a summary of the prices for {product_name} in Guatemala, including the highest and lowest prices."
    
    # Suponiendo que la API de Together recibe un cuerpo JSON con el prompt
    data = {
        "prompt": prompt,
        "prices": prices
    }
    response = requests.post("https://api.together.xyz/generate", headers=headers, json=data)
    return response.json().get("text", "")

# Interfaz de Streamlit
st.title("Comparador de Precios en Guatemala")

# Input del usuario para el nombre del producto
product_name = st.text_input("Introduce el nombre del producto:")

if st.button("Buscar Precios"):
    if product_name:
        # Obtener precios
        prices = get_prices(product_name)
        
        if prices:
            # Ordenar precios y mostrar en una tabla
            prices_sorted = sorted(prices, key=lambda x: x['price'])
            st.table(prices_sorted)
            
            # Generar y mostrar la descripción con Together
            description = generate_description(product_name, prices_sorted)
            st.write(description)
        else:
            st.write("No se encontraron precios para el producto solicitado.")
    else:
        st.write("Por favor, introduce el nombre del producto.")

