import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import streamlit as st

def get_product_info(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, features='lxml')

    try:
        title = soup.find(id='productTitle').get_text(strip=True)
    except AttributeError:
        title = 'No title found'

    try:
        image_url = soup.find(id='landingImage')['src']
    except (AttributeError, TypeError):
        image_url = None

    try:
        price_text = soup.find('span', {'class': 'a-offscreen'}).get_text(strip=True)
        price = float(price_text.replace('$', '').replace(',', ''))
    except (AttributeError, ValueError):
        price = None

    return title, image_url, price

def save_to_excel(data):
    df = pd.DataFrame(data)
    file_name = "busquedas.xlsx"

    if os.path.exists(file_name):
        existing_df = pd.read_excel(file_name)
        df = pd.concat([existing_df, df], ignore_index=True)

    df.to_excel(file_name, index=False)
    return file_name

def get_search_results(query):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    url = f"https://www.amazon.com/s?k={query.replace(' ', '+')}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, features='lxml')

    product_links = []
    for link in soup.find_all('a', {'class': 'a-link-normal s-no-outline'}, href=True):
        product_links.append("https://www.amazon.com" + link['href'])
    return product_links

# Interfaz de usuario con Streamlit
st.title("🛒 Web Scraper de Productos (Amazon)")

search_query = st.text_input("🔍 Introduce tu búsqueda:")

if search_query:
    st.write(f"### Resultados para: '{search_query}'")
    product_urls = get_search_results(search_query)

    if product_urls:
        all_data = []
        for url in product_urls[:10]:
            title, image_url, price = get_product_info(url)

            if title != 'No title found' and price is not None:
                data = {
                    'Fecha': datetime.now().strftime('%Y-%m-%d'),
                    'Título': title,
                    'Precio': price,
                    'URL Imagen': image_url,
                    "URL Producto": url
                }
                all_data.append(data)

        if all_data:
            df = pd.DataFrame(all_data)
            st.write("### 🧾 Información de los productos")
            
            # Mostrar tarjetas de productos con imagen
            for item in all_data:
                st.markdown("---")
                cols = st.columns([1, 3])
                with cols[0]:
                    if item["URL Imagen"]:
                        st.image(item["URL Imagen"], width=150)
                with cols[1]:
                    st.markdown(f"**[{item['Título']}]({item['URL Producto']})**")
                    st.markdown(f"💲 Precio: ${item['Precio']:.2f}")
                    st.markdown(f"📅 Fecha: {item['Fecha']}")

            # Botón de descarga del Excel
            file_name = save_to_excel(all_data)
            with open(file_name, "rb") as f:
                st.download_button(
                    label="📥 Descargar Excel",
                    data=f,
                    file_name=file_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            st.success(f"✅ Datos guardados en {file_name}")
        else:
            st.error("❌ No se encontraron productos válidos.")
    else:
        st.error("❌ No se encontraron resultados para tu búsqueda.")
