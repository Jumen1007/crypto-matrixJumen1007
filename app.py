import streamlit as st
import requests

# Configuración de página optimizada para Firefox Móvil
st.set_page_config(page_title="Crypto Sentiment Matrix", page_icon="📊", layout="wide")

# --- 1. LÓGICA DE APIS CON FILTRO DE FALLO SILENCIOSO ESTRICTO ---
@st.cache_data(ttl=900)  # Caché de 15 minutos
def fetch_api_data():
    """Jala datos de CoinGecko y DeFiLlama de forma totalmente aislada."""
    data = {"btc_price": 0.0, "sol_price": 0.0, "sol_tvl": 0.0}
    
    # Intento aislado para CoinGecko
    try:
        cg_url = "https://coingecko.com"
        cg_res = requests.get(cg_url, timeout=5).json()
        data["btc_price"] = cg_res.get("bitcoin", {}).get("usd", 0.0)
        data["sol_price"] = cg_res.get("solana", {}).get("usd", 0.0)
    except Exception:
        pass  # Fallo silencioso si CoinGecko no responde
        
    # Intento aislado para DeFiLlama
    try:
        df_url = "https://llama.fi"
        df_res = requests.get(df_url, timeout=5).json()
        # DeFiLlama devuelve a veces un diccionario directo o una lista de diccionarios
        if isinstance(df_res, dict):
            data["sol_tvl"] = df_res.get("tvl", 0.0)
        elif isinstance(df_res, list) and len(df_res) > 0:
            # Si es una lista, extraemos el TVL de forma segura del primer elemento
            data["sol_tvl"] = df_res[0].get("tvl", 0.0) if isinstance(df_res[0], dict) else 0.0
    except Exception:
        pass  # Fallo silencioso si DeFiLlama cambia o se cae
        
    return data

# Ejecutar llamadas de datos automatizados
api_metrics = fetch_api_data()

# --- 2. MAQUETACIÓN DE LA INTERFAZ PRINCIPAL ---
st.title("📊 Crypto Sentiment Matrix")
st.caption("Terminal táctica de sentimiento de mercado para $BTC y $SOL")

# Fila superior automatizada (Precios / Retail / Ballenas)
col_auto1, col_auto2 = st.columns(2)
with col_auto1:
    if api_metrics["btc_price"] > 0:
        st.metric(label="Bitcoin (CoinGecko)", value=f"${api_metrics['btc_price']:,} USD")
    else:
        st.warning("⚠️ Datos en tiempo real de $BTC temporalmente no disponibles (Fallo Silencioso).")

with col_auto2:
    if api_metrics["sol_price"] > 0:
        val_tvl = api_metrics['sol_tvl']
        tvl_text = f"${val_tvl/1e9:.2f}B" if val_tvl > 0 else "No disponible"
        st.metric(label="Solana (CoinGecko)", value=f"${api_metrics['sol_price']:,} USD", delta=f"TVL: {tvl_text} (DeFiLlama)")
    else:
        st.warning("⚠️ Datos en tiempo real de $SOL temporalmente no disponibles (Fallo Silencioso).")


# --- 3. ZONA EXPERTOS (INYECCIÓN MANUAL TRADERS X VÍA GROK) ---
def render_zona_expertos():
    st.markdown("---")
    st.markdown("## 🧠 Zona Expertos (Últimas 12h)")
    st.caption("Filtro analítico: Coinglass, Arkham Intelligence y CryptoQuant")

    # Variables de texto optimizadas sin errores de formato
    BTC_LIQ = "Masiva dominancia long ($404M de $436M en 4h; ~92.6%); cascada tras ruptura <$80k (low ~$79.280). Heatmaps activan liquidez densa $79.4k–$79.5k (down) y $82.2k (up)."
    BTC_FLOWS = "Transferencia on-chain récord 2026 (>230k BTC / >$21B) entre wallets privadas (no exchanges). Hashrate en alza y mineros a plena capacidad. ETF spot semanal neto +5.183 BTC."
    BTC_RANGES = "**Soporte inmediato:** $79.4k–$80.1k | **Resistencia clave:** $82.2k–$85k"

    SOL_OI = "OI estable ~$3.38B (+0.4% 24h); funding positivo (+0.0055%–0.01% 8h, longs pagan). Liquidaciones 24h ~$18–23.5M (86–87% longs)."
    SOL_FLOWS = "Sin actividad institucional o de ballenas de alto impacto detectada en la ventana filtrada por Arkham."
    SOL_RANGES = "**Soporte inmediato:** ~$100 | **Resistencia clave:** No consensuada (~$102 post-caída)"

    SINTESIS_MATRICIAL = "Sesgo institucional de acumulación lateral post-flush de longs: BTC absorbe liquidaciones y mantiene estructura sobre $79–80k con hashrate/ETF positivos, mientras SOL muestra leve sesgo long residual sin flujos on-chain relevantes."

    # Renderizado responsivo para pantallas móviles
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🪙 Bitcoin ($BTC)")
        st.error(f"**Liquidaciones:** {BTC_LIQ}")
        st.info(f"**Flujos/Ballenas:** {BTC_FLOWS}")
        st.warning(BTC_RANGES)

    with col2:
        st.markdown("### ☀️ Solana ($SOL)")
        st.error(f"**OI & Funding:** {SOL_OI}")
        st.info(f"**On-Chain:** {SOL_FLOWS}")
        st.warning(SOL_RANGES)

    st.markdown("### 📊 Síntesis de Sentimiento Matricial")
    st.success(f"**Análisis de Situación:** {SINTESIS_MATRICIAL}")

# Ejecución de la Zona Expertos
render_zona_expertos()
