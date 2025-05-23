
# ============================================
# CASO DE USO: EXPORTAR INFORMACIÓN
# DIAGRAMA DE CLASE: PDF, EXCEL Exporter
# DIAGRAMA DE SECUENCIA: Usuario -> Streamlit -> Exportador -> Librerías -> Cliente
# ============================================
import os  # Importación estándar para manejar archivos del sistema operativo
import requests  # Librería para hacer peticiones HTTP
import pandas as pd  # Librería para manipular datos en formato tabla (DataFrame)
from bs4 import BeautifulSoup  # Parser HTML para scraping
from datetime import datetime  # Para manejar fechas
import streamlit as st  # Framework para interfaces web
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage  # Componentes para generar PDFs
from reportlab.lib.pagesizes import letter  # Tamaño de hoja carta para el PDF
from reportlab.lib.styles import getSampleStyleSheet  # Estilos por defecto para el PDF
import io  # Entrada/salida de datos en memoria

# ============================================
# FUNCION PARA GENERAR PDF
# Relacionado al: Exportador PDF
# Flujo: Streamlit -> Exportador -> Librería PDF (ReportLab) -> Archivo PDF
# ============================================
def generate_pdf(data, query):
    buffer = io.BytesIO()  # Se crea un buffer en memoria para guardar el PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter)  # Se define el documento con tamaño carta
    styles = getSampleStyleSheet()  # Se obtienen estilos predefinidos
    elements = []  # Lista que contendrá los elementos del PDF

    elements.append(Paragraph(f"Resultados de búsqueda: {query}", styles['Title']))  # Título del documento
    elements.append(Spacer(1, 12))  # Espacio entre párrafos

    for item in data:  # Itera sobre cada producto
        elements.append(Paragraph(f"Título: {item['Título']}", styles['Heading4']))  # Título del producto
        elements.append(Paragraph(f"Precio: ${item['Precio']:.2f}", styles['Normal']))  # Precio del producto
        elements.append(Paragraph(f"Tienda: {item['Tienda']}", styles['Normal']))  # Tienda de origen
        elements.append(Paragraph(f"Fecha: {item['Fecha']}", styles['Normal']))  # Fecha de captura
        elements.append(Paragraph(f"URL Producto: {item['URL Producto']}", styles['Normal']))  # Enlace al producto

        if item.get("URL Imagen"):  # Si hay una imagen disponible
            try:
                response = requests.get(item["URL Imagen"], stream=True, timeout=5)  # Descarga de imagen
                if response.status_code == 200:
                    image_bytes = io.BytesIO(response.content)  # Se convierte la imagen a bytes
                    img = RLImage(image_bytes, width=100, height=100)  # Se inserta la imagen con tamaño definido
                    elements.append(img)  # Se agrega al PDF
            except Exception as e:
                elements.append(Paragraph(f"[No se pudo cargar la imagen: {e}]", styles['Normal']))  # Mensaje si falla

        elements.append(Spacer(1, 20))  # Espacio entre productos

    doc.build(elements)  # Se genera el documento PDF
    buffer.seek(0)  # Regresa al inicio del buffer
    return buffer  # Devuelve el PDF como stream

# ============================================
# CONFIGURACION DE STREAMLIT
# Relacionado al: Interfaz (controlador principal)
# ============================================
st.set_page_config(
    page_title="DealMiner",  # Título de la página
    page_icon="🛒"  # Ícono de la página
)

# ============================================
# CASO DE USO: SINCRONIZAR DATOS CON TIENDAS
# DIAGRAMA DE CLASE: Scraper -> Amazon
# DIAGRAMA DE SECUENCIA: Usuario -> Scraper -> HTML -> Datos clave
# ============================================
def get_product_info_amazon(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',  # Cabecera para evitar bloqueo
        'Accept-Language': 'en-US,en;q=0.9'
    }

    response = requests.get(url, headers=headers)  # Petición a Amazon
    soup = BeautifulSoup(response.text, features='lxml')  # Parsing del HTML

    try:
        title = soup.find(id='productTitle').get_text(strip=True)  # Extracción del título
    except AttributeError:
        title = 'No title found'  # En caso de error

    try:
        image_url = soup.find(id='landingImage')['src']  # URL de imagen del producto
    except (AttributeError, TypeError):
        image_url = None

    try:
        price_text = soup.find('span', {'class': 'a-offscreen'}).get_text(strip=True)  # Precio
        price = float(price_text.replace('$', '').replace(',', ''))
    except:
        price = None  # En caso de error

    return title, image_url, price  # Devuelve la información

# ============================================
# FUNCION PARA OBTENER RESULTADOS DE BUSQUEDA EN AMAZON
# Apoya al scraper para extraer múltiples productos
# ============================================
def get_search_results_amazon(query):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    url = f"https://www.amazon.com/s?k={query.replace(' ', '+')}"  # Construye la URL de búsqueda
    response = requests.get(url, headers=headers)  # Realiza la búsqueda
    soup = BeautifulSoup(response.text, features='lxml')  # Parseo del HTML

    product_links = []  # Lista de enlaces de productos
    for link in soup.find_all('a', {'class': 'a-link-normal s-no-outline'}, href=True):
        product_links.append("https://www.amazon.com" + link['href'])  # Agrega cada enlace completo
    return product_links

# ============================================
# FUNCION PARA EXTRAER TITULO DE UN PRODUCTO DE MERCADO LIBRE
# Parte del scraping del sitio Mercado Libre
# ============================================
def obtener_titulo_desde_pagina(url, headers):
    try:
        respuesta = requests.get(url, headers=headers)  # Solicitud HTTP al producto
        sopa = BeautifulSoup(respuesta.text, "html.parser")  # Parseo del HTML
        titulo_tag = sopa.find("h1", class_="ui-pdp-title")  # Encuentra el título del producto
        return titulo_tag.text.strip() if titulo_tag else "Sin título"  # Devuelve título o mensaje
    except:
        return "Sin título"

# ============================================
# FUNCION PARA BUSCAR PRODUCTOS EN MERCADO LIBRE
# Caso de uso: Sincronizar datos con tiendas (Scraper)
# ============================================
def buscar_en_mercado_libre(producto: str, limite=10):
    query = producto.replace(" ", "+")  # Reemplaza espacios para crear la URL de búsqueda
    url = f"https://listado.mercadolibre.com.mx/{query}"  # Construye la URL de búsqueda
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}  # Encabezado para evitar bloqueo
    respuesta = requests.get(url, headers=headers)  # Realiza la petición HTTP
    sopa = BeautifulSoup(respuesta.text, "html.parser")  # Parsea el HTML

    items = sopa.find_all("li", class_="ui-search-layout__item")  # Encuentra los items de productos
    resultados = []  # Lista para almacenar los resultados

    for item in items[:limite]:  # Limita la cantidad de resultados procesados
        try:
            enlace_tag = item.find("a", href=True)  # Encuentra el enlace del producto
            enlace = enlace_tag["href"] if enlace_tag else None
            if not enlace:
                continue

            titulo = obtener_titulo_desde_pagina(enlace, headers)  # Llama a función para obtener título

            precio_entero = item.find("span", class_="andes-money-amount__fraction")  # Parte entera del precio
            precio_decimal = item.find("span", class_="andes-money-amount__cents")  # Parte decimal del precio
            if not precio_entero:
                continue

            precio = precio_entero.text.replace(",", "")
            precio_completo = f"{precio}.{precio_decimal.text if precio_decimal else '00'}"  # Formatea el precio

            imagen_tag = item.find("img")  # Imagen del producto
            imagen = None
            if imagen_tag:
                imagen = (
                    imagen_tag.get("data-src") or
                    imagen_tag.get("data-srcset") or
                    imagen_tag.get("src")
                )

            resultados.append({
                "Fecha": datetime.now().strftime('%Y-%m-%d'),  # Fecha de captura
                "Título": titulo,
                "Precio": float(precio_completo),
                "URL Imagen": imagen,
                "URL Producto": enlace,
                "Tienda": "Mercado Libre"
            })
        except:
            continue  # Si ocurre algún error, ignora el producto actual

    return resultados  # Retorna la lista de productos encontrados
