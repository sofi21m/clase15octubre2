import json
import time
import paho.mqtt.client as mqtt
import streamlit as st

# Configuración visual de la página
st.set_page_config(
    page_title="IoT Live Telemetry",
    page_icon="⚡",
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
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
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

    with st.container(border=True):
        st.subheader("🌐 Servidor MQTT")
        broker = st.text_input('Broker Host', value='broker.mqttdashboard.com')
        port = st.number_input('Puerto', value=1883, min_value=1, max_value=65535)

    with st.container(border=True):
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
    fetch_click = st.button("🔄 Leer Sensor", use_container_width=True, type="primary")

st.divider()

# ------------------ LÓGICA DE CAPTURA ------------------
if fetch_click:
    with st.spinner("⚡ Estableciendo Handshake MQTT y leyendo canal..."):
        data = get_mqtt_message(broker, int(port), topic, client_id)
        st.session_state.sensor_data = data
        st.session_state.last_update = time.strftime("%H:%M:%S")

# ------------------ MOSTRAR RESULTADOS ------------------
if st.session_state.sensor_data is not None:
    data = st.session_state.sensor_data

    # Manejo de error
    if isinstance(data, dict) and 'error' in data:
        st.error(f"❌ **Error de Conexión:** {data['error']}")
    else:
        st.toast("¡Datos actualizados con éxito!", icon="✅")

        # Barra de estado superior
        status_col1, status_col2, status_col3 = st.columns(3)
        status_col1.caption(f"🟢 **Estado:** Conectado")
        status_col2.caption(f"🕒 **Última Lectura:** {st.session_state.last_update}")
        status_col3.caption(f"📡 **Tópico:** `{topic}`")

        st.markdown("<br>", unsafe_allow_html=True)

        # Si el payload es un objeto JSON / Dict
        if isinstance(data, dict):
            keys = list(data.keys())
            num_keys = len(keys)

            # Selección inteligente de columnas (máximo 4 por fila)
            cols_per_row = min(num_keys, 4) if num_keys > 0 else 1
            cols = st.columns(cols_per_row)

            # Iconos automáticos según la clave recibida
            def get_icon(key_name):
                key_lower = str(key_name).lower()
                if "temp" in key_lower:
                    return "🌡️"
                if "hum" in key_lower:
                    return "💧"
                if "pres" in key_lower:
                    return "🎈"
                if "volt" in key_lower or "powa" in key_lower:
                    return "⚡"
                return "📊"

            for idx, (k, v) in enumerate(data.items()):
                col_target = cols[idx % cols_per_row]
                icon = get_icon(k)

                # Formatear el valor si es flotante
                formatted_val = f"{v:.2f}" if isinstance(v, float) else str(v)

                with col_target:
                    st.markdown(
                        f"""
                        <div class="metric-card">
                            <div class="metric-title">{icon} {k}</div>
                            <div class="metric-value">{formatted_val}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    st.markdown("<br>", unsafe_allow_html=True)

            # Inspección detallada del Payload
            with st.expander("🛠️ Inspeccionar Payload JSON bruto"):
                st.json(data)

        # Si el payload es texto plano
        else:
            st.info("📩 **Payload en texto plano recibido:**")
            st.code(data, language="text")

else:
    # Estado inicial cuando no hay datos aún
    st.info("👆 Presiona **'Leer Sensor'** para conectarte al broker y obtener la última lectura.")

    with st.expander("ℹ️ Ayuda & Guía de Guía de Conexión"):
        st.markdown("""
        1. **Configura el Broker:** Ingresa los datos de conexión en el panel lateral.
        2. **Publicadores Públicos de prueba:**
           - `broker.mqttdashboard.com`
           - `broker.hivemq.com`
           - `test.mosquitto.org`
        3. Presiona el botón de actualización arriba para consumir la cola de datos.
        """)
