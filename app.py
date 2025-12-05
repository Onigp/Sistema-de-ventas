import streamlit as st
import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import base64 

# Librerías de la IA y Gestión Documental
from fpdf import FPDF
from google import genai
from google.genai.errors import APIError

# --- CONFIGURACIÓN GLOBAL Y ARCHIVOS ---
INVENTARIO_FILE = 'inventario.csv'
PEDIDOS_FILE = 'pedidos.csv'
STOCK_ALERTA = 50 
TASA_ITBMS = 0.07 
UMBRAL_DESCUENTO = 1000 
DEFAULT_COLOR = '#34495e' 
DARK_BACKGROUND = '#2c3e50' 
DARK_TEXT = '#ecf0f1' 

# --- GESTIÓN DOCUMENTAL (Carga/Guardado) ---

def cargar_datos(filename):
    """Carga datos desde CSV. Si no existe, crea un DataFrame base."""
    if os.path.exists(filename):
        return pd.read_csv(filename)
    else:
        if filename == INVENTARIO_FILE:
            return pd.DataFrame({
                'ID': ['E101', 'E102', 'E103', 'E104', 'E105'],
                'Producto': ['Cable THHN 12AWG', 'Toma Corriente Doble', 'Interruptor Sencillo', 'Regulador de Voltaje', 'Fusible 10A'],
                'Stock_Actual': [1500, 35, 400, 100, 10], 
                'Precio': [0.75, 3.50, 2.15, 45.00, 0.50], 
                'Categoría': ['Material', 'Accesorio', 'Accesorio', 'Equipo', 'Componente']
            })
        elif filename == PEDIDOS_FILE:
            return pd.DataFrame(columns=['ID_Pedido', 'Fecha', 'Producto', 'Cantidad', 'Monto_Neto', 'Monto_Total', 'Vendedor', 'Factura_Ruta'])
    return pd.DataFrame()

def guardar_datos(df, filename):
    """Guarda el DataFrame en un archivo CSV."""
    df.to_csv(filename, index=False)

# Inicializar o cargar DataFrames en la sesión de Streamlit
if 'df_inventario' not in st.session_state:
    st.session_state.df_inventario = cargar_datos(INVENTARIO_FILE)
    st.session_state.df_pedidos = cargar_datos(PEDIDOS_FILE)
    st.session_state.feed_mensajes = [("🔒 [CIBERSEGURIDAD] Sistema iniciado. MFA activo.", 'blue')]
    st.session_state.carrito = [] # NUEVO: Inicializar el carrito de compras

# Guardar automáticamente los datos al finalizar o al recargar
guardar_datos(st.session_state.df_inventario, INVENTARIO_FILE)
guardar_datos(st.session_state.df_pedidos, PEDIDOS_FILE)

# --- INICIALIZACIÓN DE LA IA (Gemini - CONFIGURACIÓN SEGURA) ---
client = None
api_key_secure = st.secrets.get("GEMINI_API_KEY") 

if api_key_secure:
    try:
        client = genai.Client(api_key=api_key_secure)
    except Exception as e:
        st.error(f"Error al inicializar la API de Gemini. Verifique la clave en secrets.toml. Error: {e}")
        client = None
else:
    pass 


# --- CLASES Y UTILIDADES ---

class PDF(FPDF):
    """Clase personalizada para el diseño del PDF (Factura)."""
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'ElectroPanamá Solutions - Factura Electrónica', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def get_binary_file_downloader_html(bin_file, file_label='Descargar Archivo', file_name='factura.pdf'):
    """Genera un botón de descarga para un archivo binario (PDF) en Streamlit."""
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    # Estilo del botón de descarga integrado en HTML/CSS
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{file_name}" style="background-color: #2ecc71; color: white; padding: 0.5em 1em; text-decoration: none; border-radius: 5px; font-size: 14px;">{file_label}</a>'
    return href

def create_download_link(row):
    """Genera el HTML para el botón de descarga del PDF."""
    ruta = row['Factura_Ruta']
    if os.path.exists(ruta):
        # Utiliza la función get_binary_file_downloader_html ya definida
        html_link = get_binary_file_downloader_html(ruta, 
                                                    file_label='⬇️ Descargar', 
                                                    file_name=os.path.basename(ruta))
        return html_link
    return "N/A"


# --- LÓGICA DE NEGOCIO Y FLUJO DIGITAL ---

def generar_documento_factura(pedido_info, df_carrito):
    """Crea un archivo .pdf detallado que simula la factura electrónica (Gestión Documental)."""
    
    factura_id = f"F{datetime.now().strftime('%Y%m%d%H%M%S')}"
    ruta_factura = f"facturas/{factura_id}.pdf"
    
    if not os.path.exists("facturas"):
        os.makedirs("facturas")
    
    pdf = PDF('P', 'mm', 'Letter')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Colores y fuentes
    pdf.set_fill_color(52, 73, 94) 
    pdf.set_text_color(255, 255, 255) 
    pdf.set_font('Arial', 'B', 12)
    
    pdf.cell(0, 8, 'DATOS DE LA TRANSACCIÓN', 1, 1, 'C', 1)
    
    pdf.set_text_color(0, 0, 0) 
    pdf.set_font('Arial', '', 10)
    pdf.cell(50, 6, 'FACTURA ID:', 0, 0)
    pdf.cell(0, 6, factura_id, 0, 1)
    pdf.cell(50, 6, 'FECHA:', 0, 0)
    pdf.cell(0, 6, pedido_info['Fecha'], 0, 1)
    pdf.cell(50, 6, 'VENDEDOR:', 0, 0)
    pdf.cell(0, 6, pedido_info['Vendedor'], 0, 1)
    pdf.ln(5)
    
    # Detalles del Producto (Tabla simple)
    pdf.set_fill_color(220, 220, 220) 
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(100, 7, 'Producto', 1, 0, 'C', 1)
    pdf.cell(30, 7, 'Cantidad (Uds)', 1, 0, 'C', 1)
    pdf.cell(35, 7, 'P. Unitario ($)', 1, 0, 'C', 1)
    pdf.cell(30, 7, 'Subtotal ($)', 1, 1, 'C', 1)
    
    pdf.set_font('Arial', '', 10)
    
    # ITERACIÓN DE MÚLTIPLES PRODUCTOS DEL CARRITO
    for index, item in df_carrito.iterrows():
        pdf.cell(100, 6, item['Producto'], 1, 0)
        pdf.cell(30, 6, str(item['Cantidad']), 1, 0, 'C')
        pdf.cell(35, 6, f"{item['Precio_Unitario']:.2f}", 1, 0, 'R')
        pdf.cell(30, 6, f"{item['Subtotal_Bruto']:.2f}", 1, 1, 'R')
        
    pdf.ln(8)
    
    # Resumen de Montos
    ancho_label = 50
    ancho_valor = 30
    margen = 135 
    
    pdf.set_x(margen)
    pdf.cell(ancho_label, 6, 'SUBTOTAL BRUTO:', 0, 0, 'L')
    pdf.cell(ancho_valor, 6, f"${df_carrito['Subtotal_Bruto'].sum():.2f}", 0, 1, 'R')

    if pedido_info['Descuento'] > 0:
        pdf.set_x(margen)
        pdf.cell(ancho_label, 6, 'DESCUENTO (10%):', 0, 0, 'L')
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(ancho_valor, 6, f"-${pedido_info['Descuento']:.2f}", 0, 1, 'R')
        pdf.set_font('Arial', '', 10) 
    
    pdf.set_x(margen)
    pdf.cell(ancho_label, 6, 'SUBTOTAL NETO:', 0, 0, 'L')
    pdf.cell(ancho_valor, 6, f"${pedido_info['Monto_Neto']:.2f}", 0, 1, 'R')
    
    pdf.set_x(margen)
    pdf.cell(ancho_label, 6, f"ITBMS ({TASA_ITBMS*100:.0f}%):", 0, 0, 'L')
    pdf.cell(ancho_valor, 6, f"${pedido_info['Monto_ITBMS']:.2f}", 0, 1, 'R')

    pdf.set_font('Arial', 'B', 12)
    pdf.set_x(margen)
    pdf.set_fill_color(52, 73, 94) 
    pdf.set_text_color(255, 255, 255) 
    pdf.cell(ancho_label, 8, 'TOTAL A PAGAR:', 1, 0, 'L', 1)
    pdf.cell(ancho_valor, 8, f"${pedido_info['Monto_Total']:.2f}", 1, 1, 'R', 1)
    
    pdf.output(ruta_factura)
    return ruta_factura


def procesar_venta_multiple(df_carrito, vendedor_id, monto_neto, monto_total_final, descuento_valor, monto_itbms):
    """Maneja el Flujo Digital de Venta, Inventario, Automatización y Facturación para múltiples productos."""
    
    # 1. Validación de stock 
    for index, item in df_carrito.iterrows():
        stock_actual = st.session_state.df_inventario[st.session_state.df_inventario['ID'] == item['ID']]['Stock_Actual'].iloc[0]
        if item['Cantidad'] > stock_actual:
            st.error(f"❌ Venta abortada: Stock insuficiente para {item['Producto']}. Por favor, revise el inventario.")
            return False

    # 2. Facturación y Pago Digital
    pedido_info_dict = {
        'Fecha': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'Vendedor': vendedor_id,
        'Monto_Neto': monto_neto,
        'Monto_ITBMS': monto_itbms,
        'Monto_Total': monto_total_final,
        'Descuento': descuento_valor
    }
    
    ruta_factura = generar_documento_factura(pedido_info_dict, df_carrito)

    # 3. Actualizar Inventario y DataFrames de Pedidos
    
    for index, item in df_carrito.iterrows():
        # Actualiza el stock
        st.session_state.df_inventario.loc[st.session_state.df_inventario['ID'] == item['ID'], 'Stock_Actual'] -= item['Cantidad'] 
        
        # Agrega un registro para CADA ítem vendido (para mantener la trazabilidad en df_pedidos)
        nuevo_pedido = pd.DataFrame([{
            'ID_Pedido': f"P{datetime.now().strftime('%Y%m%d%H%M%S')}-{index}", # ID único por ítem
            'Fecha': pedido_info_dict['Fecha'],
            'Producto': item['Producto'],
            'Cantidad': item['Cantidad'],
            'Monto_Neto': item['Subtotal_Bruto'], # Guarda el subtotal bruto del ítem
            'Monto_Total': item['Subtotal_Bruto'], # Se actualiza en el reporte
            'Vendedor': vendedor_id,
            'Factura_Ruta': ruta_factura 
        }])
        st.session_state.df_pedidos = pd.concat([st.session_state.df_pedidos, nuevo_pedido], ignore_index=True)

    # 4. Comunicación y Feedback
    mensaje_desc = f" (Desc.: ${descuento_valor:.2f})" if descuento_valor > 0 else ""

    st.success(f"✅ VENTA MULTIPLE CERRADA por {vendedor_id}: TOTAL FINAL: ${monto_total_final}{mensaje_desc}")
    st.info(f"Ruta de Factura (Gestión Documental PDF): {ruta_factura}.")
    
    st.markdown(get_binary_file_downloader_html(ruta_factura, 
                                                file_label='⬇️ Descargar Factura Consolidada PDF',
                                                file_name=os.path.basename(ruta_factura)), 
                unsafe_allow_html=True)
    
    st.session_state.feed_mensajes.append((f"💰 [VENTAS] Pedido (Múltiple) facturado por {vendedor_id}. Total: ${monto_total_final:.2f}{mensaje_desc}", 'blue'))
    
    return True


# --- FUNCIÓN DE ALERTA PREDICTIVA (IA BÁSICA) ---
def obtener_alerta_predictiva(df_inventario, df_pedidos):
    """Calcula una alerta predictiva del stock restante en días, basado en la velocidad de venta promedio."""
    
    if df_pedidos.empty:
        return pd.DataFrame() 

    df_pedidos['Fecha'] = pd.to_datetime(df_pedidos['Fecha'])
    dias_operacion = (df_pedidos['Fecha'].max() - df_pedidos['Fecha'].min()).days
    periodo_dias = max(dias_operacion, 7) 
    
    df_ventas = df_pedidos.groupby('Producto')['Cantidad'].sum().reset_index()
    df_ventas['Velocidad_Venta_Dia'] = df_ventas['Cantidad'] / periodo_dias
    df_ventas = df_ventas.rename(columns={'Cantidad': 'Total_Vendido'})
    
    df_analisis = pd.merge(df_inventario, df_ventas, on='Producto', how='left').fillna(0)
    
    # Usa 'Stock_Actual', que es el nombre de columna que llega a esta función
    df_analisis['Dias_Restantes'] = np.where(
        df_analisis['Velocidad_Venta_Dia'] > 0.01,
        df_analisis['Stock_Actual'] / df_analisis['Velocidad_Venta_Dia'], 
        999 
    )

    df_alerta_final = df_analisis[df_analisis['Dias_Restantes'] <= 14] 
    
    return df_alerta_final.sort_values(by='Dias_Restantes')

# --- FUNCIONES DE DASHBOARD Y REPORTES ---

def generar_graficas():
    """Genera las 4 gráficas requeridas."""
    df_p = st.session_state.df_pedidos
    df_i = st.session_state.df_inventario
    
    cols = st.columns(2)

    # Gráfica 1: Tendencia de Ventas (KPI Tasa de Conversión)
    with cols[0]:
        st.subheader("📈 Tendencia de Ventas (30 días)")
        if df_p.shape[0] > 0 and 'Fecha' in df_p.columns:
            df_p['Fecha_DT'] = pd.to_datetime(df_p['Fecha'])
            ventas_diarias = df_p.set_index('Fecha_DT')['Monto_Total'].resample('D').sum().fillna(0).tail(30)
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.plot(ventas_diarias.index.strftime('%m-%d'), ventas_diarias.values, marker='o', color='#2ecc71')
            ax.set_title("Ventas por Día", fontsize=10, color=DARK_TEXT)
            ax.set_ylabel("Monto ($)", color=DARK_TEXT)
            ax.tick_params(axis='x', rotation=45, colors=DARK_TEXT)
            ax.tick_params(axis='y', colors=DARK_TEXT)
            ax.set_facecolor(DARK_BACKGROUND)
            fig.set_facecolor(DARK_BACKGROUND)
            st.pyplot(fig)
        else:
            st.warning("No hay datos de ventas para Tendencia.")

    # Gráfica 2: Ventas por Vendedor (KPI)
    with cols[1]:
        st.subheader("👥 Ventas por Vendedor")
        if df_p.shape[0] > 0:
            # Aquí sumamos Monto_Total aunque no sea el valor final exacto, para KPI rápido
            ventas_vendedor = df_p.groupby('Vendedor')['Monto_Total'].sum().sort_values(ascending=False) 
            fig, ax = plt.subplots(figsize=(6, 4))
            ventas_vendedor.plot(kind='bar', ax=ax, color='#3498db')
            ax.set_title("Total Vendido por Empleado", fontsize=10, color=DARK_TEXT)
            ax.set_ylabel("Monto Total ($)", color=DARK_TEXT)
            ax.tick_params(axis='x', rotation=0, colors=DARK_TEXT)
            ax.tick_params(axis='y', colors=DARK_TEXT)
            ax.set_facecolor(DARK_BACKGROUND)
            fig.set_facecolor(DARK_BACKGROUND)
            st.pyplot(fig)
        else:
            st.warning("No hay datos de ventas por vendedor.")

    cols2 = st.columns(2)
    
    # Gráfica 3: Stock Valorizado (KPI Inventario)
    with cols2[0]:
        st.subheader("💰 Stock Valorizado (Top 5)")
        df_i['Valor_Total'] = df_i['Stock_Actual'] * df_i['Precio'] 
        top_valor = df_i.nlargest(5, 'Valor_Total')
        if not top_valor.empty:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.pie(top_valor['Valor_Total'], labels=top_valor['ID'] + ' (' + top_valor['Producto'].str[:15] + '...)', autopct='%1.1f%%', startangle=90, colors=plt.cm.Set3.colors, textprops={'color': DARK_TEXT})
            ax.set_title("Distribución del Valor del Inventario", fontsize=10, color=DARK_TEXT)
            fig.set_facecolor(DARK_BACKGROUND)
            st.pyplot(fig)
        else:
            st.warning("No hay datos de stock valorizado.")

    # Gráfica 4: Stock Actual (KPI Rotación)
    with cols2[1]:
        st.subheader("📦 Stock Actual (Unidades)")
        top_stock = df_i.nlargest(5, 'Stock_Actual') 
        if not top_stock.empty:
            fig, ax = plt.subplots(figsize=(6, 4))
            colors = ['#e74c3c' if s <= STOCK_ALERTA else '#2ecc71' for s in top_stock['Stock_Actual']]
            ax.bar(top_stock['ID'] + ' - ' + top_stock['Producto'].str[:10] + '...', top_stock['Stock_Actual'], color=colors)
            ax.set_title("Top 5 Items con Mayor Stock", fontsize=10, color=DARK_TEXT)
            ax.set_ylabel("Unidades", color=DARK_TEXT)
            ax.tick_params(axis='x', rotation=45, labelsize=8, colors=DARK_TEXT)
            ax.tick_params(axis='y', colors=DARK_TEXT)
            ax.set_facecolor(DARK_BACKGROUND)
            fig.set_facecolor(DARK_BACKGROUND)
            st.pyplot(fig)
        else:
            st.warning("No hay datos de stock.")
    # ...

def agregar_item_inventario(nuevo_id, nuevo_prod, nuevo_stock, nuevo_precio, nueva_cat):
    """Función para agregar un nuevo ítem al inventario."""
    if nuevo_id in st.session_state.df_inventario['ID'].values:
        st.error("❌ Error: ID de producto ya existente.")
        return
        
    try:
        nuevo_stock = int(nuevo_stock)
        nuevo_precio = float(nuevo_precio)
    except ValueError:
        st.error("❌ Error: Stock y Precio deben ser valores numéricos válidos.")
        return

    nuevo_item = pd.DataFrame([{
        'ID': nuevo_id,
        'Producto': nuevo_prod,
        'Stock_Actual': nuevo_stock,
        'Precio': nuevo_precio,
        'Categoría': nueva_cat
    }])
    st.session_state.df_inventario = pd.concat([st.session_state.df_inventario, nuevo_item], ignore_index=True)
    st.success(f"✅ Ítem **{nuevo_id}** agregado al inventario.")

def enviar_notificacion(area, mensaje):
    """Simula el envío de una notificación a un área específica."""
    if 'feed_mensajes' not in st.session_state:
        st.session_state.feed_mensajes = []
    
    color = 'orange'
    st.session_state.feed_mensajes.append((f"🔔 [{area.upper()}] {mensaje}", color))
    st.info(f"Mensaje enviado a '{area}'.")

def generar_reporte_imprimible(tipo_reporte):
    """Genera un reporte imprimible (CSV/TXT) para descarga."""
    if tipo_reporte == 'INVENTARIO':
        reporte_data = st.session_state.df_inventario.copy()
        titulo = "REPORTE_INVENTARIO_STOCK"
    elif tipo_reporte == 'VENTAS':
        reporte_data = st.session_state.df_pedidos.copy()
        titulo = "REPORTE_VENTAS_DETALLE"
    else:
        return

    csv = reporte_data.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=f"Descargar {tipo_reporte} (CSV)",
        data=csv,
        file_name=f"{titulo}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime='text/csv',
        key=f'download_btn_{tipo_reporte}'
    )
    st.success(f"Reporte de {tipo_reporte} listo para descarga.")

# --- INTERFAZ STREAMLIT (FLUIDA Y MODERNA) ---

st.set_page_config(layout="wide", page_title="Sistema PYME Panamá", page_icon="⚙️")

# Estilos CSS
st.markdown(f"""
<style>
.stApp {{ background-color: {DARK_BACKGROUND}; color: {DARK_TEXT}; }}
.stSidebar {{ background-color: {DEFAULT_COLOR}; }}
h1, h2, h3, h4 {{ color: {DARK_TEXT}; }}
.css-1y4pz5l {{ color: white !important; }}
p, label {{ color: {DARK_TEXT}; }}
.stTabs [data-baseweb="tab-list"] button {{ background-color: {DARK_BACKGROUND}; color: {DARK_TEXT}; }}
[data-testid="stTextInput"] > div > input, [data-testid="stNumberInput"] > div > input,
[data-testid="stSelectbox"] div[role="button"] {{ background-color: #3f516a; color: {DARK_TEXT}; }}
/* Estilo para la tabla de pedidos con HTML */
.dataframe th {{ background-color: {DEFAULT_COLOR} !important; color: white; }}
.dataframe td {{ padding: 8px 10px; }}
.dataframe tr:nth-child(even) {{ background-color: #3f516a; }}
</style>
""", unsafe_allow_html=True)


# --- BARRA LATERAL (KPI y Comunicación) ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: white;'>⚙️ GESTIÓN PYME</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # KPI 1: Alerta de Inventario (KPI)
    stock_alerta_count = st.session_state.df_inventario[st.session_state.df_inventario['Stock_Actual'] <= STOCK_ALERTA].shape[0]
    
    if stock_alerta_count > 0:
        st.error(f"🚨 {stock_alerta_count} ÍTEMS EN STOCK CRÍTICO")
    else:
        st.success("✅ INVENTARIO OK")
    
    st.warning("🔒 **CIBERSEGURIDAD**: MFA Activo (Google Workspace)")
    st.markdown("---")
    
    # --- FEED DE COMUNICACIÓN ---
    st.markdown("### 💬 Feed de Comunicación")
    if 'feed_mensajes' in st.session_state:
        for mensaje, color in reversed(st.session_state.feed_mensajes[-8:]): 
            if color == 'blue':
                st.markdown(f'<p style="color:#3498db; font-size: 14px;">{mensaje}</p>', unsafe_allow_html=True)
            elif color == 'green':
                st.markdown(f'<p style="color:#2ecc71; font-size: 14px;">{mensaje}</p>', unsafe_allow_html=True)
            elif color == 'orange':
                st.markdown(f'<p style="color:#f39c12; font-size: 14px;">{mensaje}</p>', unsafe_allow_html=True)
            else:
                st.markdown(f'<p style="color:white; font-size: 14px;">{mensaje}</p>', unsafe_allow_html=True)
    
    # Botón de Alerta de Tiempos
    if st.button("Simular Alerta Tiempos Muertos (Flujo)", key='btn_alerta_tiempos', type="primary"):
        enviar_notificacion("GERENCIA/TÉCNICO", "TAREA ATASCADA: Pedido más antiguo lleva > 48h sin avance.")
        st.rerun() 

# --- PESTAÑAS PRINCIPALES ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["💵 Venta y Facturación", "📦 Gestión de Inventario", "📈 Dashboard de KPIs", "📑 Reportes y SC", "⭐ **IA: Generación**"])

# --- TAB 1: VENTA Y FACTURACIÓN (Flujo Digital) ---
with tab1:
    st.header("Flujo Digital: Carrito de Compras y Facturación")
    
    # 1. ENTRADA DEL CARRITO
    st.subheader("🛒 Agregar Productos al Carrito")
    col_id, col_cant = st.columns([3, 1])

    productos_disponibles = st.session_state.df_inventario.copy()
    productos_disponibles['Display'] = productos_disponibles['ID'] + ' - ' + productos_disponibles['Producto'] + ' (Stock: ' + productos_disponibles['Stock_Actual'].astype(str) + ')'
    
    with col_id:
        producto_seleccionado = st.selectbox("Producto (ID - Nombre)", productos_disponibles['Display'], key='select_prod')
        
    with col_cant:
        cantidad = st.number_input("Cantidad", min_value=1, step=1, value=1, key='input_cant')
    
    id_producto = producto_seleccionado.split(' - ')[0] if producto_seleccionado else None
    
    if st.button("➕ Añadir al Carrito", key='btn_add_to_cart', type="secondary"):
        
        producto_info = st.session_state.df_inventario[st.session_state.df_inventario['ID'] == id_producto]
        
        if producto_info.empty:
            st.error("❌ ID de producto no válido.")
        else:
            stock_actual = producto_info['Stock_Actual'].iloc[0]
            if cantidad > stock_actual:
                st.warning(f"⚠️ Stock Insuficiente. Solo hay {stock_actual} uds.")
            else:
                # Agregar ítem al carrito
                item_carrito = {
                    'ID': id_producto,
                    'Producto': producto_info['Producto'].iloc[0],
                    'Cantidad': cantidad,
                    'Precio_Unitario': producto_info['Precio'].iloc[0],
                    'Subtotal_Bruto': cantidad * producto_info['Precio'].iloc[0]
                }
                st.session_state.carrito.append(item_carrito)
                st.success(f"✅ Añadido: {cantidad} x {item_carrito['Producto']} al carrito.")
                st.rerun() 
    
    st.markdown("---")
    
    # 2. VISUALIZACIÓN Y FACTURACIÓN DEL CARRITO
    st.subheader("🛍️ Carrito Actual")

    if st.session_state.carrito:
        df_carrito = pd.DataFrame(st.session_state.carrito)
        
        # Calcular totales
        monto_subtotal = df_carrito['Subtotal_Bruto'].sum()
        
        # Lógica de descuento
        descuento = 0
        mensaje_desc = " "
        if monto_subtotal >= UMBRAL_DESCUENTO:
            descuento = round(monto_subtotal * 0.10, 2)
            mensaje_desc = "(10% de descuento aplicado)"

        monto_neto = monto_subtotal - descuento
        monto_itbms = round(monto_neto * TASA_ITBMS, 2)
        monto_total_final = round(monto_neto + monto_itbms, 2)

        # Mostrar Carrito y Resumen
        st.dataframe(df_carrito[['Producto', 'Cantidad', 'Precio_Unitario', 'Subtotal_Bruto']].rename(columns={'Subtotal_Bruto': 'Subtotal'}), hide_index=True, use_container_width=True)
        
        col_resumen, col_factura = st.columns([1, 1])
        with col_resumen:
            st.markdown(f"""
                <div style="padding: 10px; border: 1px solid #34495e; border-radius: 5px;">
                <p>Subtotal Bruto: <b>${monto_subtotal:,.2f}</b></p>
                <p style="color:#e74c3c;">Descuento {mensaje_desc}: <b>-${descuento:,.2f}</b></p>
                <p>Subtotal Neto: <b>${monto_neto:,.2f}</b></p>
                <p>ITBMS ({TASA_ITBMS*100:.0f}%): <b>+${monto_itbms:,.2f}</b></p>
                <h3 style="color:#2ecc71;">TOTAL FINAL: ${monto_total_final:,.2f}</h3>
                </div>
            """, unsafe_allow_html=True)
        
        with col_factura:
            vendedor_id_factura = st.text_input("Vendedor (ID)", value="V01", key='factura_vendedor')
            if st.button("PASO FINAL: FACTURAR Y COBRAR", key='btn_facturar_multi', type="primary"):
                procesar_venta_multiple(df_carrito, vendedor_id_factura, monto_neto, monto_total_final, descuento, monto_itbms)
                # Limpiar carrito después de facturar
                st.session_state.carrito = [] 
                st.rerun()
                
            if st.button("Vaciar Carrito", key='btn_clear_cart', type="secondary"):
                st.session_state.carrito = []
                st.rerun()
                
    else:
        st.info("El carrito de compras está vacío.")

    st.markdown("---")
    st.subheader("📑 Registro de Pedidos (Gestión Documental)")
    
    # Lógica para mostrar la tabla con los botones de descarga
    df_pedidos_display = st.session_state.df_pedidos.copy()
    
    if not df_pedidos_display.empty:
        # 1. Crea la columna del enlace de descarga
        df_pedidos_display['Descargar'] = df_pedidos_display.apply(create_download_link, axis=1)
        
        columnas_a_mostrar = ['ID_Pedido', 'Fecha', 'Producto', 'Cantidad', 'Monto_Total', 'Vendedor', 'Descargar']
        
        # 2. Usa st.write con .to_html(escape=False) para renderizar el HTML del botón
        st.write(
            df_pedidos_display[columnas_a_mostrar].to_html(escape=False, index=False),
            unsafe_allow_html=True
        )
    else:
        st.info("No hay pedidos registrados aún.")


# --- TAB 2: GESTIÓN DE INVENTARIO ---
with tab2:
    st.header("Gestión de Inventario: Agregar y Visualizar Stock")
    
    # Agregar Ítem
    with st.expander("✅ Agregar Nuevo Ítem al Inventario", expanded=False):
        col_new_id, col_new_prod, col_new_cat, col_new_stock, col_new_price = st.columns(5)
        
        with col_new_id:
            new_id = st.text_input("ID de Producto", key='new_id')
        with col_new_prod:
            new_prod = st.text_input("Nombre del Producto", key='new_prod')
        with col_new_cat:
            new_cat = st.text_input("Categoría", value='General', key='new_cat')
        with col_new_stock:
            new_stock = st.text_input("Stock Inicial", value='0', key='new_stock')
        with col_new_price:
            new_price = st.text_input("Precio Unitario", value='0.00', key='new_price')

        if st.button("GUARDAR ITEM", key='btn_add_item', type="secondary"):
            if new_id and new_prod:
                agregar_item_inventario(new_id.upper(), new_prod, new_stock, new_price, new_cat)
                st.rerun() 
            else:
                st.error("Los campos ID y Producto son obligatorios.")

    # Inventario Maestro
    st.subheader("📦 Inventario Maestro (Stock y Precio)")
    
    # Función de estilo para stock crítico
    def color_stock(row):
        style = [''] * len(row)
        if 'Stock' in row and row['Stock'] <= STOCK_ALERTA: 
            style = ['background-color: #8c2525; color: white'] * len(row) 
        return style

    # Se renombra Stock_Actual a Stock para que el estilo funcione y se muestre mejor
    st.dataframe(st.session_state.df_inventario.rename(columns={'Stock_Actual': 'Stock'}).style.apply(color_stock, axis=1), use_container_width=True)
    st.caption("Filas resaltadas indican **Stock Crítico** (KPI: <= 50 unidades).")

# --- TAB 3: DASHBOARD DE KPIS ---
with tab3:
    st.header("Dashboard de KPIs y Métricas Valiosas")
    
    # KPIs en cajas
    total_ventas = st.session_state.df_pedidos['Monto_Total'].sum()
    promedio_pedido = st.session_state.df_pedidos['Monto_Total'].mean() if st.session_state.df_pedidos.shape[0] > 0 else 0
    df_i_temp = st.session_state.df_inventario.copy()
    df_i_temp['Valor_Total'] = df_i_temp['Stock_Actual'] * df_i_temp['Precio']
    valor_inventario = df_i_temp['Valor_Total'].sum()
    
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("Total Ventas", f"${total_ventas:,.2f}")
    col_kpi2.metric("Pedido Promedio", f"${promedio_pedido:,.2f}")
    col_kpi3.metric("Stock Valorizado", f"${valor_inventario:,.2f}")
    
    st.markdown("---")
    
    # Integración de la IA Básica (Predictiva)
    st.subheader("💡 Alerta Predictiva de Stock (IA Básica)")
    
    # Llama a la función con el nombre de columna original ('Stock_Actual')
    df_predictivo = obtener_alerta_predictiva(st.session_state.df_inventario.copy(), st.session_state.df_pedidos.copy())

    if not df_predictivo.empty:
        st.warning(f"🚨 **¡Atención!** {len(df_predictivo)} productos podrían agotarse en menos de 14 días al ritmo actual de venta.")
        
        # Renombrar 'Stock_Actual' a 'Stock' justo antes de mostrar
        df_predictivo = df_predictivo.rename(columns={'Stock_Actual': 'Stock'})
        
        st.dataframe(
            df_predictivo[['Producto', 'Stock', 'Velocidad_Venta_Dia', 'Dias_Restantes']],
            column_config={
                "Producto": "Producto",
                "Stock": "Stock Actual",
                "Velocidad_Venta_Dia": "Venta Promedio (Unidades/Día)",
                "Dias_Restantes": st.column_config.NumberColumn("Días Estimados Restantes", format="%.1f días")
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.success("Inventario estable. Ningún producto está en riesgo de agotarse rápidamente (predicción > 14 días).")
    
    st.divider() 
    
    generar_graficas()

# --- TAB 4: REPORTES Y COMUNICACIÓN ---
with tab4:
    st.header("Generación de Reportes y Comunicación Inter-Áreas")

    # Comunicación a Áreas
    with st.form(key='form_notificacion'):
        col_area, col_msg = st.columns([1, 3])
        
        with col_area:
            area = st.selectbox("Área", ['VENTAS', 'GERENCIA', 'TÉCNICO', 'ADMINISTRACIÓN'], key='notif_area_form')
        
        with col_msg:
            mensaje = st.text_input("Mensaje", key='notif_msg_form')
        
        submit_button = st.form_submit_button(label="ENVIAR", type="secondary")

        if submit_button:
            if mensaje:
                enviar_notificacion(area, mensaje)
                st.rerun() 
            else:
                st.error("El mensaje no puede estar vacío.")

    st.markdown("---")

    # Reportes Imprimibles
    st.subheader("🖨️ Reportes Imprimibles (CSV - Gestión Documental)")
    col_rep1, col_rep2, col_sc = st.columns(3)
    
    with col_rep1:
        generar_reporte_imprimible('INVENTARIO')
    with col_rep2:
        generar_reporte_imprimible('VENTAS')
    with col_sc:
        if st.button("Simular Envío Feedback (Servicio al Cliente)", key='btn_sim_sc'):
            enviar_notificacion("SERVICIO AL CLIENTE", "Solicitud de Feedback (CSAT) enviada al último cliente.")
            st.rerun()

# --- TAB 5: IA REAL (GENERACIÓN DE CONTENIDO) ---
with tab5:
    st.header("⭐ Generador de Contenido de Marketing (Gemini)")
    
    if client is None:
        st.error("⚠️ La funcionalidad de IA no está disponible.")
        st.caption("Verifique: 1) **Instalación** de `google-genai`. 2) **Clave API** en el archivo seguro `.streamlit/secrets.toml`.")
    else:
        st.info("Utilice la IA para generar descripciones de producto, publicaciones de redes sociales o ideas de venta usando el modelo Gemini 2.5 Flash (Free Tier).")

        productos = st.session_state.df_inventario['Producto'].unique().tolist()
        
        producto_seleccionado = st.selectbox("Seleccione el Producto a promocionar:", productos)

        if producto_seleccionado:
            detalles = st.session_state.df_inventario[
                st.session_state.df_inventario['Producto'] == producto_seleccionado
            ].iloc[0]
            
            st.markdown(f"**Detalles:** Stock: {detalles['Stock_Actual']}, Precio: **${detalles['Precio']:.2f}**, Categoría: {detalles['Categoría']}")

            tarea = st.text_area(
                "Instrucción para la IA (Prompt):",
                value=f"Genera una publicación de Instagram (máx. 50 palabras y 3 emojis) para promocionar nuestro producto '{producto_seleccionado}'. Menciona su precio de ${detalles['Precio']:.2f} y enfócate en la calidad y la necesidad en Panamá.",
                height=150
            )

            if st.button("✨ Generar Mensaje de Marketing", type="primary"):
                if tarea:
                    with st.spinner('Contactando con Gemini...'):
                        try:
                            response = client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=tarea
                            )
                            st.subheader("Resultado de la IA:")
                            st.success(response.text)
                            
                        except APIError as e:
                            st.error(f"Error de la API: {e}. Puede ser un error de la clave o que se excedió el límite de uso gratuito.")
                        except Exception as e:
                            st.error(f"Error inesperado: {e}")
                else:
                    st.error("Por favor, escriba una instrucción para la IA.")