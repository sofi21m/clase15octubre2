import json
import time
import paho.mqtt.client as mqtt
import streamlit as st

# Configuración visual de la página
st.set_page_config(
    page_title="IoT Live Telemetry",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para tarjetas elegantes e indicadores
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.01));
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        text-align: center;
    }
    .metric-title {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #A0AEC0;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #00E676;
    }
</style>
""", unsafe_allow_html=True)

# Variables de estado
if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = None
if 'last_update' not in st.session_state:
    st.session_state.last_update = None


def get_mqtt_message(broker, port, topic, client_id):
    """Obtiene el payload más reciente mediante suscripción temporal."""
    message_received = {"received": False, "payload": None}

    def on_message(client, userdata, message):
        raw_payload = message.payload.decode()
        try:
            message_received["payload"] = json.loads(raw_payload)
        except Exception:
            message_received["payload"] = raw_payload
        message_received["received"] = True

    try:
        # Compatibilidad con Paho MQTT v1 y v2
        try:
            client = mqtt.Client(paho.CallbackAPIVersion.VERSION1, client_id=client_id)
        except AttributeError:
            client = mqtt.Client(client_id=client_id)

        client.on_message = on_message
        client.connect(broker, port, 60)
        client.subscribe(topic)
        client.loop_start()

        timeout = time.time() + 4.0
        while not message_received["received"] and time.time() < timeout:
            time.sleep(0.05)

        client.loop_stop()
        client.disconnect()

        return message_received["payload"]

    except Exception as e:
        return {"error": str(e)}


# ------------------ SIDEBAR (Configuración) ------------------
with st.sidebar:
    st.title("🎛️ Panel de Control")
    st.caption("Configuración de Broker & Telemetría")

    st.subheader("🌐 Servidor MQTT")
    broker = st.text_input('Broker Host', value='broker.mqttdashboard.com')
    port = st.number_input('Puerto', value=1883, min_value=1, max_value=65535)

    st.markdown("---")
    st.subheader("📡 Tópico y Cliente")
    topic = st.text_input('Tópico', value='Sensor/THP2')
    client_id = st.text_input('ID de Cliente', value='streamlit_monitor')

    st.markdown("---")
    st.markdown("💡 **Tip:** Asegúrate de que el broker acepte conexiones sin TLS en el puerto 1883.")


# ------------------ HEADER ------------------
col_title, col_btn = st.columns([3, 1], vertical_alignment="bottom")

with col_title:
    st.title("📡 Dashboard de Telemetría IoT")
    st.caption("Visualización de métricas en tiempo real a través del protocolo MQTT")

with col_btn:
    fetch_click = st.button("🔄 Leer Sensor", use_container_width=True
