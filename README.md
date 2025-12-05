⚙️ ElectroPanamá Solutions: Sistema de Gestión PYME (Ventas & Inventario)
Bienvenido al sistema de gestión digital para pequeñas y medianas empresas (PYME), enfocado en el control de inventario, el flujo de ventas con facturación electrónica (simulada en PDF), y la integración de Inteligencia Artificial para alertas predictivas y marketing.

✨ Características Destacadas
Flujo de Ventas Digital: Sistema de Carrito de Compras que permite facturar múltiples productos en una sola transacción.

Gestión Documental: Generación automática de Facturas PDF consolidadas para cada venta, disponibles para descarga inmediata.

Automatización: Aplicación de un descuento del 10% automático para pedidos superiores a $1000 USD.

Inteligencia Operacional (KPIs): Dashboard con métricas clave y una Alerta Predictiva de Stock (IA Básica) para pronosticar ítems críticos.

Integración de IA (Gemini): Herramienta para generar contenido de marketing (descripciones, publicaciones) de forma instantánea.

🛠️ Configuración y Requisitos
Para correr la aplicación, necesitarás Python, Git y las librerías específicas.

1. Instalación de Dependencias
Asegúrate de instalar todas las librerías listadas en el archivo requirements.txt.

Bash

pip install -r requirements.txt
2. Configuración de la API de Gemini (IA)
Para usar la funcionalidad de marketing por IA, debes configurar tu clave de forma segura:

Crea la carpeta .streamlit en la raíz del proyecto.

Dentro de ella, crea un archivo llamado secrets.toml.

Pega tu clave API en este archivo:

Ini, TOML

# .streamlit/secrets.toml
GEMINI_API_KEY="AIzaSy...TuClaveCompletaDeGemini...XyZ"
Asegúrate de que el archivo .gitignore excluya .streamlit/secrets.toml para proteger tu clave en GitHub.

▶️ Ejecución Local
Una vez configurado, ejecuta la aplicación Streamlit desde la terminal en la carpeta raíz del proyecto:

Bash

streamlit run app.py
Esto abrirá la aplicación en tu navegador predeterminado (normalmente en http://localhost:8501).

☁️ Despliegue en Streamlit Community Cloud
Para desplegar la aplicación en la nube (la forma más recomendada para compartirla), sigue estos pasos esenciales:

Sube el código base (app.py, requirements.txt, .gitignore) a un repositorio de GitHub.

Ve a Streamlit Community Cloud e inicia el despliegue desde tu repositorio.

En la configuración de la aplicación (sección "Advanced settings" -> "Secrets"), ingresa la clave de tu API de Gemini. Debes usar el nombre de variable exacto:

GEMINI_API_KEY="TU_CLAVE_API_DE_GEMINI_AQUI"
👨‍💻 Guía de Uso Rápido
El sistema está dividido en pestañas para gestionar los diferentes flujos del negocio:

1. 💵 Venta y Facturación
Carrito de Compras: Utiliza la interfaz de selección para añadir múltiples productos al carrito.

Facturar y Cobrar: Al hacer clic en el botón principal, se procesa la venta, se actualiza el inventario, y se genera una única factura PDF consolidada para todos los ítems del carrito.

Historial: La tabla inferior muestra el registro de pedidos con enlaces de descarga de las facturas.

2. 📦 Gestión de Inventario
Permite ver el stock actual y añadir nuevos productos. El stock crítico (<= 50 unidades) se resalta visualmente.

3. 📈 Dashboard de KPIs
Métricas Clave: Muestra el rendimiento en ventas, el valor del inventario, y gráficas de tendencia.

Alerta Predictiva: Identifica automáticamente los productos con alto riesgo de agotamiento (menos de 14 días de stock, según el ritmo histórico de venta).

4. ⭐ IA: Generación
Selecciona un producto y pide a la IA (Gemini 2.5 Flash) que genere mensajes de marketing, publicaciones para redes sociales, o descripciones de producto.
