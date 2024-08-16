import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Configuración de las APIs (las claves se obtienen de los secretos de Streamlit)
TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]
SERPER_API_KEY = st.secrets["SERPER_API_KEY"]

def get_product_prices(producto_especifico=None):
    if producto_especifico:
        prompt = f"Proporciona el precio actual en Guatemala del producto: {producto_especifico}. Si no tienes información exacta, proporciona un estimado basado en productos similares. Incluye el nombre del producto y su precio en quetzales."
    else:
        prompt = "Proporciona una lista de 10 productos comunes en Guatemala con sus precios actuales, ordenados del más caro al más barato. Incluye el nombre del producto y su precio en quetzales."
    
    response = requests.post(
        "https://api.together.xyz/inference",
        headers={
            "Authorization": f"Bearer {TOGETHER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "togethercomputer/llama-2-70b-chat",
            "prompt": prompt,
            "max_tokens": 512,
            "temperature": 0.7
        }
    )
    
    ai_response = response.json()["output"]["choices"][0]["text"]
    
    # Procesamiento de la respuesta para crear un DataFrame
    lines = ai_response.strip().split('\n')
    data = []
    for line in lines:
        parts = line.split(' - Q')
        if len(parts) == 2:
            product = parts[0].strip()
            price = float(parts[1].replace(',', '').strip())
            data.append({"Producto": product, "Precio (Q)": price})
    
    df = pd.DataFrame(data)
    if not producto_especifico:
        df = df.sort_values("Precio (Q)", ascending=False)
    
    return df

# Interfaz de Streamlit
st.title("Precios de Productos en Guatemala")

producto_especifico = st.text_input("Especifica un producto (opcional)")

if st.button("Obtener precios"):
    df = get_product_prices(producto_especifico)
    
    if df.empty:
        st.warning("No se encontró información para el producto especificado.")
    else:
        st.subheader("Tabla de Precios")
        st.table(df)

        if len(df) > 1:
            st.subheader("Gráfico de Precios")
            st.bar_chart(df.set_index("Producto"))

        # Información adicional sobre la fecha de actualización
        st.info(f"Información actualizada al: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

        st.warning("Nota: Estos precios son aproximados y pueden variar según la ubicación y el proveedor.")

    # Búsqueda adicional usando Serper API
    if producto_especifico:
        st.subheader("Resultados de búsqueda adicionales")
        serper_response = requests.post(
            "https://google.serper.dev/search",
            headers={
                "X-API-KEY": SERPER_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "q": f"precio {producto_especifico} Guatemala"
            }
        )
        
        search_results = serper_response.json()["organic"][:3]  # Tomamos los primeros 3 resultados
        for result in search_results:
            st.write(f"- [{result['title']}]({result['link']})")
            st.write(result['snippet'])
