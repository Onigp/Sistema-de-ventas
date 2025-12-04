import streamlit as st
import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
# Librería para generar PDFs
from fpdf import FPDF 
# Librería para manejo de archivos binarios para descarga
import base64 

# --- CONFIGURACIÓN GLOBAL ---
INVENTARIO_FILE = 'inventario.csv'
PEDIDOS_FILE = 'pedidos.csv'
STOCK_ALERTA = 50 
TASA_ITBMS = 0.07 
UMBRAL_DESCUENTO = 1000 
DEFAULT_COLOR = '#34495e' # Azul oscuro elegante
DARK_BACKGROUND = '#2c3e50' # Gris oscuro para fondo de modo oscuro
DARK_TEXT = '#ecf0f1' # Gris claro para texto

# --- 1. GESTIÓN DOCUMENTAL (Carga/Guardado) ---

def cargar_datos(filename):
    """Carga datos desde CSV. Si no existe, crea un DataFrame base."""
    if os.path.exists(filename):
        return pd.read_csv(filename)
    else:
        if filename == INVENTARIO_FILE:
            return pd.DataFrame({
                'ID': ['E101', 'E102', 'E103', 'E104', 'E105'],
                'Producto': ['Cable THHN 12AWG', 'Toma Corriente Doble', 'Interruptor Sencillo', 'Regulador de Voltaje', 'Fusible 10A'],
                'Stock': [1500, 35, 400, 100, 10],
                'Precio_Unitario': [0.75, 3.50, 2.15, 45.00, 0.50]
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

# Guardar automáticamente los datos al finalizar o al recargar (simulación de persistencia)
guardar_datos(st.session_state.df_inventario, INVENTARIO_FILE)
guardar_datos(st.session_state.df_pedidos, PEDIDOS_FILE)

# --- 2. LÓGICA DE NEGOCIO Y FLUJO DIGITAL (Con Generación de PDF) ---

class PDF(FPDF):
    """Clase personalizada para el diseño del PDF."""
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'ElectroPanamá Solutions - Factura Electrónica', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def generar_documento_factura(pedido_info):
    """Crea un archivo .pdf detallado que simula la factura electrónica (Gestión Documental)."""
    
    factura_id = f"F{datetime.now().strftime('%Y%m%d%H%M%S')}"
    ruta_factura = f"facturas/{factura_id}.pdf"
    
    if not os.path.exists("facturas"):
        os.makedirs("facturas")
    
    pdf = PDF('P', 'mm', 'Letter')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Estilos del encabezado de la factura
    pdf.set_fill_color(52, 73, 94) 
    pdf.set_text_color(255, 255, 255) 
    pdf.set_font('Arial', 'B', 12)
    
    pdf.cell(0, 8, 'DATOS DE LA TRANSACCIÓN', 1, 1, 'C', 1)
    
    # Cuerpo de la Factura
    pdf.set_text_color(0, 0, 0) 
    pdf.set_font('Arial', '', 10)
    
    pdf.cell(50, 6, 'FACTURA ID:', 0, 0)
    pdf.cell(0, 6, factura_id, 0, 1)
    
    pdf.cell(50, 6, 'FECHA:', 0, 0)
    pdf.cell(0, 6, pedido_info['Fecha'], 0, 1)
    
    pdf.cell(50, 6, 'VENDEDOR:', 0, 0)
    pdf.cell(0, 6, pedido_info['Vendedor'], 0, 1)
    pdf.ln(5)
    
    # --- Detalles del Producto ---
    pdf.set_fill_color(220, 220, 220) 
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(100, 7, 'Producto', 1, 0, 'C', 1)
    pdf.cell(30, 7, 'Cantidad (Uds)', 1, 0, 'C', 1)
    pdf.cell(35, 7, 'P. Unitario ($)', 1, 0, 'C', 1)
    pdf.cell(30, 7, 'Subtotal ($)', 1, 1, 'C', 1)
    
    pdf.set_font('Arial', '', 10)
    
    # Buscar el precio unitario original
    producto_info = st.session_state.df_inventario[st.session_state.df_inventario['Producto'] == pedido_info['Producto']]
    precio_unitario_original = producto_info['Precio_Unitario'].iloc[0] if not producto_info.empty else 0.00
        
    pdf.cell(100, 6, pedido_info['Producto'], 1, 0)
    pdf.cell(30, 6, str(pedido_info['Cantidad']), 1, 0, 'C')
    pdf.cell(35, 6, f"{precio_unitario_original:.2f}", 1, 0, 'R')
    
    subtotal_bruto = pedido_info['Monto_Neto']
    if 'Descuento' in pedido_info and pedido_info['Descuento'] > 0:
        subtotal_bruto += pedido_info['Descuento'] 
        
    pdf.cell(30, 6, f"{subtotal_bruto:.2f}", 1, 1, 'R')
    pdf.ln(8)
    
    # --- Resumen de Montos ---
    ancho_label = 50
    ancho_valor = 30
    margen = 135 
    
    pdf.set_x(margen)
    pdf.cell(ancho_label, 6, 'SUBTOTAL NETO:', 0, 0, 'L')
    pdf.cell(ancho_valor, 6, f"${pedido_info['Monto_Neto']:.2f}", 0, 1, 'R')
    
    if 'Descuento' in pedido_info and pedido_info['Descuento'] > 0:
        pdf.set_x(margen)
        pdf.cell(ancho_label, 6, 'DESCUENTO (10%):', 0, 0, 'L')
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(ancho_valor, 6, f"-${pedido_info['Descuento']:.2f}", 0, 1, 'R')
        pdf.set_font('Arial', '', 10) 
    
    pdf.set_x(margen)
    pdf.cell(ancho_label, 6, f"ITBMS ({TASA_ITBMS*100:.0f}%):", 0, 0, 'L')
    monto_itbms = pedido_info['Monto_Total'] - pedido_info['Monto_Neto']
    pdf.cell(ancho_valor, 6, f"${monto_itbms:.2f}", 0, 1, 'R')

    pdf.set_font('Arial', 'B', 12)
    pdf.set_x(margen)
    pdf.set_fill_color(52, 73, 94) # Color de fondo
    pdf.set_text_color(255, 255, 255) # Texto blanco
    pdf.cell(ancho_label, 8, 'TOTAL A PAGAR:', 1, 0, 'L', 1)
    pdf.cell(ancho_valor, 8, f"${pedido_info['Monto_Total']:.2f}", 1, 1, 'R', 1)
    
    pdf.output(ruta_factura)
    return ruta_factura

def get_binary_file_downloader_html(bin_file, file_label='Descargar Archivo', file_name='factura.pdf'):
    """Genera un botón de descarga para un archivo binario (PDF) en Streamlit."""
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{file_name}" style="background-color: #2ecc71; color: white; padding: 0.5em 1em; text-decoration: none; border-radius: 5px;">{file_label}</a>'
    return href

def procesar_venta(id_producto, vendedor_id, cantidad):
    """Maneja el Flujo Digital de Venta, Inventario, Automatización y Facturación."""
    
    # 1. Validación de Inventario
    producto_info = st.session_state.df_inventario[st.session_state.df_inventario['ID'] == id_producto]
    
    if producto_info.empty:
        st.error("❌ ID de producto no válido.")
        return False
        
    stock_actual = producto_info['Stock'].iloc[0]
    precio = producto_info['Precio_Unitario'].iloc[0]
    if cantidad > stock_actual:
        st.warning(f"⚠️ Stock Insuficiente (Paso 2 del Flujo). Solo hay {stock_actual} uds.")
        return False

    # 2. Automatización (Descuento por volumen)
    monto_bruto = cantidad * precio
    monto_neto = monto_bruto
    descuento_valor = 0
    mensaje_desc = ""
    
    if monto_bruto >= UMBRAL_DESCUENTO:
        descuento_valor = monto_bruto * 0.10
        monto_neto -= descuento_valor
        mensaje_desc = " (10% Desc. Aplicado por Automatización IA)"

    # 3. Facturación y Pago Digital
    monto_itbms = monto_neto * TASA_ITBMS
    monto_total_final = round(monto_neto + monto_itbms, 2)
    
    pedido_info_dict = {
        'Fecha': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'Vendedor': vendedor_id,
        'Producto': producto_info['Producto'].iloc[0],
        'Cantidad': cantidad,
        'Monto_Neto': round(monto_neto, 2),
        'Monto_ITBMS': round(monto_itbms, 2),
        'Monto_Total': monto_total_final,
        'Descuento': round(descuento_valor, 2)
    }
    ruta_factura = generar_documento_factura(pedido_info_dict)

    # 4. Actualizar DataFrames (Inventario y Pedidos)
    st.session_state.df_inventario.loc[st.session_state.df_inventario['ID'] == id_producto, 'Stock'] -= cantidad
    
    nuevo_pedido = pd.DataFrame([{
        'ID_Pedido': f"P{datetime.now().strftime('%Y%m%d%H%M%S')}",
        'Fecha': pedido_info_dict['Fecha'],
        'Producto': pedido_info_dict['Producto'],
        'Cantidad': cantidad,
        'Monto_Neto': pedido_info_dict['Monto_Neto'],
        'Monto_Total': monto_total_final,
        'Vendedor': vendedor_id,
        'Factura_Ruta': ruta_factura 
    }])
    st.session_state.df_pedidos = pd.concat([st.session_state.df_pedidos, nuevo_pedido], ignore_index=True)

    # 5. Comunicación y Feedback
    st.success(f"✅ VENTA CERRADA por {vendedor_id}: TOTAL FINAL: ${monto_total_final}{mensaje_desc}")
    st.info(f"Ruta de Factura (Gestión Documental PDF): {ruta_factura}. Simulación de **Pago Digital/Wallet** enviada.")
    
    # Mostrar el botón de descarga del PDF
    st.markdown(get_binary_file_downloader_html(ruta_factura, 
                                                file_label='⬇️ Descargar Factura PDF',
                                                file_name=os.path.basename(ruta_factura)), 
                unsafe_allow_html=True)
    
    # Agregar mensaje al feed de comunicación
    st.session_state.feed_mensajes.append((f"💰 [VENTAS] Pedido facturado por {vendedor_id}. Monto: ${monto_total_final:.2f}{mensaje_desc}", 'blue'))
    
    return True

# --- 3. FUNCIONES DE DASHBOARD (Gráficas) ---

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
            ax.set_facecolor(DARK_BACKGROUND) # Fondo del gráfico
            fig.set_facecolor(DARK_BACKGROUND) # Fondo de la figura
            st.pyplot(fig)
        else:
            st.warning("No hay datos de ventas para Tendencia.")

    # Gráfica 2: Ventas por Vendedor (KPI)
    with cols[1]:
        st.subheader("👥 Ventas por Vendedor")
        if df_p.shape[0] > 0:
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
        df_i['Valor_Total'] = df_i['Stock'] * df_i['Precio_Unitario']
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
        top_stock = df_i.nlargest(5, 'Stock')
        if not top_stock.empty:
            fig, ax = plt.subplots(figsize=(6, 4))
            colors = ['#e74c3c' if s <= STOCK_ALERTA else '#2ecc71' for s in top_stock['Stock']]
            ax.bar(top_stock['ID'] + ' - ' + top_stock['Producto'].str[:10] + '...', top_stock['Stock'], color=colors)
            ax.set_title("Top 5 Items con Mayor Stock", fontsize=10, color=DARK_TEXT)
            ax.set_ylabel("Unidades", color=DARK_TEXT)
            ax.tick_params(axis='x', rotation=45, labelsize=8, colors=DARK_TEXT)
            ax.tick_params(axis='y', colors=DARK_TEXT)
            ax.set_facecolor(DARK_BACKGROUND)
            fig.set_facecolor(DARK_BACKGROUND)
            st.pyplot(fig)
        else:
            st.warning("No hay datos de stock.")


# --- 4. GESTIÓN DE INVENTARIO (Funcional) ---

def agregar_item_inventario(nuevo_id, nuevo_prod, nuevo_stock, nuevo_precio):
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
        'Stock': nuevo_stock,
        'Precio_Unitario': nuevo_precio
    }])
    st.session_state.df_inventario = pd.concat([st.session_state.df_inventario, nuevo_item], ignore_index=True)
    st.success(f"✅ Ítem **{nuevo_id}** agregado al inventario.")

# --- 5. COMUNICACIÓN Y REPORTES ---

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
    st.success(f"Reporte de {tipo_reporte} listo para descarga (Simulación de Impresión/Exportación).")


# --- INTERFAZ STREAMLIT (FLUIDA Y MODERNA) ---

st.set_page_config(layout="wide", page_title="Sistema PYME Panamá", page_icon="⚙️")

# Estilos CSS para Streamlit
# Usamos un tema oscuro para un look moderno y profesional
st.markdown(f"""
<style>
.stApp {{
    background-color: {DARK_BACKGROUND};
    color: {DARK_TEXT};
}}
.stSidebar {{
    background-color: {DEFAULT_COLOR};
}}
h1, h2, h3, h4 {{
    color: {DARK_TEXT};
}}
/* Estilo para el título en la sidebar */
.css-1y4pz5l {{ 
    color: white !important;
}}
/* Asegurar que el texto general sea claro */
p, label {{
    color: {DARK_TEXT}; 
}}
/* Ajustar el fondo de las pestañas para modo oscuro */
.stTabs [data-baseweb="tab-list"] button {{
    background-color: {DARK_BACKGROUND};
    color: {DARK_TEXT};
}}
/* Ajustar los campos de entrada */
[data-testid="stTextInput"] > div > input,
[data-testid="stNumberInput"] > div > input {{
    background-color: #3f516a; /* Un tono más claro que el fondo */
    color: {DARK_TEXT};
}}
/* Ajustar los selectbox/dropdowns */
[data-testid="stSelectbox"] div[role="button"] {{
    background-color: #3f516a;
    color: {DARK_TEXT};
}}
</style>
""", unsafe_allow_html=True)


# --- BARRA LATERAL (KPI y Comunicación) ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: white;'>⚙️ GESTIÓN PYME</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # KPI 1: Alerta de Inventario (KPI y Ciberseguridad)
    stock_alerta_count = st.session_state.df_inventario[st.session_state.df_inventario['Stock'] <= STOCK_ALERTA].shape[0]
    
    if stock_alerta_count > 0:
        st.error(f"🚨 {stock_alerta_count} ÍTEMS EN STOCK CRÍTICO")
    else:
        st.success("✅ INVENTARIO OK")
    
    st.warning("🔒 **CIBERSEGURIDAD**: MFA Activo (Google Workspace)")
    st.markdown("---")

    st.markdown("### 💬 Feed de Comunicación")
    # Feed de Comunicación 
    if 'feed_mensajes' in st.session_state:
        for mensaje, color in reversed(st.session_state.feed_mensajes[-8:]): 
            if color == 'blue':
                st.markdown(f'<p style="color:#3498db; font-size: 14px;">{mensaje}</p>', unsafe_allow_html=True)
            elif color == 'green':
                st.markdown(f'<p style="color:#2ecc71; font-size: 14px;">{mensaje}</p>', unsafe_allow_html=True)
            elif color == 'orange':
                st.markdown(f'<p style="color:#f39c12; font-size: 14px;">{mensaje}</p>', unsafe_allow_html=True)
            else:
                st.markdown(f'<p style="color:{DARK_TEXT}; font-size: 14px;">{mensaje}</p>', unsafe_allow_html=True)
    
    # Botón de Alerta de Tiempos
    if st.button("Simular Alerta Tiempos Muertos (Flujo)", key='btn_alerta_tiempos', type="primary"):
        enviar_notificacion("GERENCIA/TÉCNICO", "TAREA ATASCADA: Pedido más antiguo lleva > 48h sin avance.")
        st.rerun() 

# --- PESTAÑAS PRINCIPALES ---
tab1, tab2, tab3, tab4 = st.tabs(["💵 Venta y Facturación", "📦 Gestión de Inventario", "📈 Dashboard de KPIs", "📑 Reportes y SC"])

# --- TAB 1: VENTA Y FACTURACIÓN (Flujo Digital) ---
with tab1:
    st.header("Flujo Digital: Procesar Venta y Generar Factura")
    
    col_v, col_id, col_cant = st.columns(3)
    
    with col_v:
        vendedor_id = st.text_input("Vendedor (ID)", value="V01", key='venta_vendedor')
    with col_id:
        # Solo productos con stock > 0
        productos_disponibles = st.session_state.df_inventario[st.session_state.df_inventario['Stock'] > 0]
        opciones_id = productos_disponibles['ID'].tolist()
        
        if not opciones_id:
            st.error("No hay productos disponibles para la venta.")
            id_producto = None
        else:
            opciones_display = [f"{id} - {prod}" for id, prod in zip(productos_disponibles['ID'], productos_disponibles['Producto'])]
            producto_seleccionado = st.selectbox("Producto (ID - Nombre)", opciones_display)
            id_producto = producto_seleccionado.split(' - ')[0] if producto_seleccionado else None
            
    with col_cant:
        cantidad = st.number_input("Cantidad a Vender", min_value=1, step=1, value=1)
        
    if id_producto and st.button("PASO FINAL: FACTURAR Y COBRAR (Simulación Wallet)", key='btn_procesar_venta', type="primary"):
        if cantidad > 0:
            procesar_venta(id_producto, vendedor_id, cantidad)
            st.rerun() 
        else:
            st.error("La cantidad debe ser mayor a cero.")

    st.markdown("---")
    st.subheader("📑 Registro de Pedidos (Gestión Documental)")
    # Se ajusta el dataframe para que se vea mejor en modo oscuro
    st.dataframe(st.session_state.df_pedidos, use_container_width=True)

# --- TAB 2: GESTIÓN DE INVENTARIO ---
with tab2:
    st.header("Gestión de Inventario: Agregar y Visualizar Stock")
    
    # Agregar Ítem
    with st.expander("✅ Agregar Nuevo Ítem al Inventario", expanded=False):
        col_new_id, col_new_prod, col_new_stock, col_new_price = st.columns(4)
        
        with col_new_id:
            new_id = st.text_input("ID de Producto", key='new_id')
        with col_new_prod:
            new_prod = st.text_input("Nombre del Producto", key='new_prod')
        with col_new_stock:
            new_stock = st.text_input("Stock Inicial", value='0', key='new_stock')
        with col_new_price:
            new_price = st.text_input("Precio Unitario", value='0.00', key='new_price')

        if st.button("GUARDAR ITEM", key='btn_add_item', type="secondary"):
            if new_id and new_prod:
                agregar_item_inventario(new_id.upper(), new_prod, new_stock, new_price)
                st.rerun() 
            else:
                st.error("Los campos ID y Producto son obligatorios.")

    # Inventario Maestro
    st.subheader("📦 Inventario Maestro (Stock y Precio)")
    
    # Resaltar filas con stock bajo (función de estilo de pandas)
    def color_stock(row):
        style = [''] * len(row)
        if row['Stock'] <= STOCK_ALERTA:
            style = ['background-color: #8c2525; color: white'] * len(row) # Rojo oscuro para modo oscuro
        return style

    st.dataframe(st.session_state.df_inventario.style.apply(color_stock, axis=1), use_container_width=True)
    st.caption("Filas resaltadas indican **Stock Crítico** (KPI: <= 50 unidades).")

# --- TAB 3: DASHBOARD DE KPIS ---
with tab3:
    st.header("Dashboard de KPIs y Métricas Valiosas")
    
    # KPIs en cajas
    total_ventas = st.session_state.df_pedidos['Monto_Total'].sum()
    promedio_pedido = st.session_state.df_pedidos['Monto_Total'].mean() if st.session_state.df_pedidos.shape[0] > 0 else 0
    df_i_temp = st.session_state.df_inventario.copy()
    df_i_temp['Valor_Total'] = df_i_temp['Stock'] * df_i_temp['Precio_Unitario']
    valor_inventario = df_i_temp['Valor_Total'].sum()
    
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("Total Ventas", f"${total_ventas:,.2f}")
    col_kpi2.metric("Pedido Promedio", f"${promedio_pedido:,.2f}")
    col_kpi3.metric("Stock Valorizado", f"${valor_inventario:,.2f}")
    
    st.markdown("---")
    
    generar_graficas()

# --- TAB 4: REPORTES Y COMUNICACIÓN (Optimizado con st.form) ---
with tab4:
    st.header("Generación de Reportes y Comunicación Inter-Áreas")

    # Comunicación a Áreas (Usando st.form para manejo de estado limpio)
    st.subheader("🔔 Enviar Notificación a Área Específica")
    
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

def get_binary_file_downloader_html(bin_file, file_label='Descargar Archivo', file_name='factura.pdf'):
    """Genera un botón de descarga para un archivo binario (PDF) en Streamlit."""
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{file_name}" style="background-color: #2ecc71; color: white; padding: 0.5em 1em; text-decoration: none; border-radius: 5px;">{file_label}</a>'
    return href

# ...existing code...
def listar_archivos_facturas():
    """Devuelve lista de rutas de facturas (pdf o txt) ordenadas por fecha (desc)."""
    dir_fact = "facturas"
    if not os.path.exists(dir_fact):
        return []
    archivos = [f for f in sorted(os.listdir(dir_fact), reverse=True) if f.lower().endswith(('.pdf', '.txt'))]
    return [os.path.join(dir_fact, f) for f in archivos]

def mostrar_factura_ui(container):
    """UI pequeña para seleccionar, abrir (nueva pestaña) o descargar la factura seleccionada."""
    facturas = listar_archivos_facturas()
    if not facturas:
        container.info("No hay facturas generadas aún.")
        return

    opciones = [os.path.basename(f) for f in facturas]
    seleccion = container.selectbox("Facturas disponibles", opciones, key='select_factura_streamlit')
    ruta_sel = facturas[opciones.index(seleccion)]

    # Si es PDF -> permitir abrir en nueva pestaña (data URI) y descarga
    if ruta_sel.lower().endswith('.pdf'):
        with open(ruta_sel, 'rb') as fh:
            data_bin = fh.read()
        b64 = base64.b64encode(data_bin).decode()
        # enlace para abrir en nueva pestaña
        href_open = f'<a href="data:application/pdf;base64,{b64}" target="_blank" style="margin-right:8px;">🔍 Abrir en nueva pestaña</a>'
        container.markdown(href_open, unsafe_allow_html=True)
        # botón de descarga nativo de Streamlit
        container.download_button("⬇️ Descargar PDF", data_bin, file_name=os.path.basename(ruta_sel), mime='application/pdf')
    else:
        # txt u otros -> mostrar contenido y permitir descarga de texto
        with open(ruta_sel, 'r', encoding='utf-8', errors='ignore') as fh:
            txt = fh.read()
        container.download_button("⬇️ Descargar (TXT)", txt.encode('utf-8'), file_name=os.path.basename(ruta_sel), mime='text/plain')
        container.code(txt, language='text')

# ...existing code...
with tab1:
    st.header("Flujo Digital: Procesar Venta y Generar Factura")
    
    col_v, col_id, col_cant = st.columns(3)
    # ...existing code...
    st.markdown("---")
    st.subheader("📑 Registro de Pedidos (Gestión Documental)")
    # Se ajusta el dataframe para que se vea mejor en modo oscuro
    st.dataframe(st.session_state.df_pedidos, use_container_width=True)

    # --- Nueva sección: Acceder facturas generadas desde la app ---
    with st.expander("📂 Acceder Factura Generada", expanded=False):
        mostrar_factura_ui(st)
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