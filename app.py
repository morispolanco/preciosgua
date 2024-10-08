import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import re

# Configuración de las APIs (las claves se obtienen de los secretos de Streamlit)
TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]
SERPER_API_KEY = st.secrets["SERPER_API_KEY"]

def parse_price(price_str):
    # Elimina cualquier carácter que no sea dígito, punto o guion
    price_str = re.sub(r'[^\d.-]', '', price_str)
    try:
        if '-' in price_str:
            # Si es un rango, calcula el promedio
            low, high = map(float, price_str.split('-'))
            return (low + high) / 2
        else:
            return float(price_str)
    except ValueError:
        # Si no se puede convertir a float, retorna None
        return None

def get_product_prices(producto_especifico=None):
    if producto_especifico:
        prompt = f"""Actúa como un experto en precios de productos en Guatemala. 
        Proporciona el precio estimado en quetzales para el producto: {producto_especifico}. 
        Si no tienes información exacta, da un rango de precios basado en productos similares. 
        Formato de respuesta: 'Producto: [nombre], Precio estimado: Q[precio] o Rango: Q[min]-Q[max]'
        Si no puedes encontrar información, responde 'No se encontró información para {producto_especifico}'."""
    else:
        prompt = """Actúa como un experto en precios de productos en Guatemala. 
        Proporciona una lista de 10 productos comunes con sus precios actuales estimados, ordenados del más caro al más barato. 
        Formato de respuesta para cada producto: 'Producto: [nombre], Precio estimado: Q[precio]'"""

    try:
        response = requests.post(
            "https://api.together.xyz/inference",
            headers={
                "Authorization": f"Bearer {TOGETHER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "togethercomputer/llama-2-70b-chat",
                "prompt": prompt,
                "max_tokens": 1024,
                "temperature": 0.7
            }
        )
        response.raise_for_status()
        ai_response = response.json()["output"]["choices"][0]["text"].strip()
    except requests.RequestException as e:
        st.error(f"Error al conectar con la API: {str(e)}")
        return pd.DataFrame()
    
    if "No se encontró información" in ai_response:
        return pd.DataFrame()
    
    # Procesamiento de la respuesta para crear un DataFrame
    lines = ai_response.split('\n')
    data = []
    for line in lines:
        if 'Producto:' in line and 'Precio estimado:' in line:
            parts = line.split(',')
            product = parts[0].split(':')[1].strip()
            price_part = parts[1].split(':')[1].strip()
            price = parse_price(price_part)
            if price is not None:
                data.append({"Producto": product, "Precio (Q)": price})
    
    df = pd.DataFrame(data)
    if not producto_especifico and not df.empty:
        df = df.sort_values("Precio (Q)", ascending=False)
    
    return df

# Interfaz de Streamlit
st.title("Precios de Productos en Guatemala")

producto_especifico = st.text_input("Especifica un producto (opcional)")

if st.button("Obtener precios"):
    with st.spinner("Buscando información de precios..."):
        df = get_product_prices(producto_especifico)
    
    if df.empty:
        st.warning(f"No se encontró información para el producto: {producto_especifico}")
    else:
        st.subheader("Información de Precios")
        st.table(df)

        if len(df) > 1:
            st.subheader("Gráfico de Precios")
            st.bar_chart(df.set_index("Producto"))

        # Información adicional sobre la fecha de actualización
        st.info(f"Información estimada al: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    # Búsqueda adicional usando Serper API
    if producto_especifico:
        st.subheader("Resultados de búsqueda adicionales")
        try:
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
            serper_response.raise_for_status()
            search_results = serper_response.json().get("organic", [])[:3]  # Tomamos los primeros 3 resultados
            if search_results:
                for result in search_results:
                    st.write(f"- [{result['title']}]({result['link']})")
                    st.write(result['snippet'])
            else:
                st.write("No se encontraron resultados adicionales.")
        except requests.RequestException as e:
            st.error(f"Error al buscar información adicional: {str(e)}")

st.markdown("---")
st.warning("""
Nota importante:
- Los precios mostrados son estimaciones basadas en IA y pueden no reflejar los precios reales actuales.
- Los precios pueden variar significativamente según la ubicación, el proveedor y las condiciones del mercado.
- Para obtener precios precisos, se recomienda consultar directamente con los vendedores o tiendas locales.
""")
