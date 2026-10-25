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
# --- 3. ZONA EXPERTOS (MÁQUINA ALGORÍTMICA MULTI-CRYPTO)
def limpiar_valores_csv(valor):
    """Convierte strings con M, K y N/A a flotantes puros para cálculos"""
    val_str = str(valor).strip().upper()
    if val_str in ['N/A', 'NONE', '']:
        return 0.0
    try:
        if 'M' in val_str:
            return float(val_str.replace('M', '')) * 1_000_000
        if 'K' in val_str:
            return float(val_str.replace('K', '')) * 1_000
        return float(val_str)
    except ValueError:
        return 0.0

def render_zona_expertos(datos_entrada):
    try:
        data_str = datos_entrada.strip()
        if data_str.startswith("```csv"):
            data_str = data_str.replace("```csv", "").replace("```", "").strip()
        
        import io
        df = pd.read_csv(io.StringIO(data_str))
        df.columns = df.columns.str.strip()
        
        columnas_num = ['liq_longs', 'liq_shorts', 'net_flow_ballenas', 'oi_change_pct', 'funding_rate']
        for col in columnas_num:
            if col in df.columns:
                df[col] = df[col].apply(limpiar_valores_csv)
            else:
                df[col] = 0.0
        
        df['score_liq'] = ((df['liq_shorts'] - df['liq_longs']) / (df['liq_longs'] + df['liq_shorts'] + 1e-5)) * 50
        df['score_oi'] = df['oi_change_pct'] * 10
        df['score_flows'] = np.where(df['net_flow_ballenas'] > 0, -20, 20)
        df['score_flows'] = np.where(df['net_flow_ballenas'] == 0, 0, df['score_flows'])
        
        df['SCORE_TOTAL'] = (df['score_liq'] + df['score_oi'] + df['score_flows']).clip(-100, 100)
        
        condiciones = [
            (df['SCORE_TOTAL'] >= 15),
            (df['SCORE_TOTAL'] <= -15)
        ]
        direcciones = ['🚀 Probable Subida (Presión Cortos)', '⚠️ Probable Bajada (Presión Largos)']
        df['DIRECCIÓN'] = np.select(condiciones, direcciones, default='🔄 Consolidación / Neutro')
        
        st.markdown("## 📊 Resultados del Screener Multi-Crypto")
        
        for _, row in df.iterrows():
            ticker = row['ticker'].strip().upper()
            score = row['SCORE_TOTAL']
            direccion = row['DIRECCIÓN']
            
            if "Subida" in direccion:
                box_render = st.success
            elif "Bajada" in direccion:
                box_render = st.error
            else:
                box_render = st.warning
            
            box_render(f"**{ticker}** | Score Algorítmico: **{score:.1f}%** | {direccion}")
            
            with st.expander(f"Ver métricas duras procesadas para {ticker}"):
                st.write(f"• Liquidaciones Longs: ${row['liq_longs']:,.2f}")
                st.write(f"• Liquidaciones Shorts: ${row['liq_shorts']:,.2f}")
                st.write(f"• Ratio de Desequilibrio de Fuerza: {row['score_liq']:.1f}%")
                
    except Exception as e:
        st.error(f"Error al procesar el bloque de datos CSV: {str(e)}")

# --- INTERFAZ DE USUARIO FINAL EN PRODUCCIÓN (Sin sangría inicial)
st.markdown("---")
st.subheader("🧠 Zona Expertos: Inyección de Datos CSV (Perplexity)")

with st.form(key="expert_data_form", clear_on_submit=False):
    grok_raw_input = st.text_area(
        label="Pega aquí el bloque de código CSV copiado de Perplexity:",
        height=250,
        placeholder="ticker,liq_longs,liq_shorts..."
    )
    submit_button = st.form_submit_button(label="⚡ Ejecutar Screener Algorítmico")

if submit_button:
    if grok_raw_input.strip() != "":
        render_zona_expertos(grok_raw_input)
    else:
        st.warning("El recuadro está vacío. Copia y pega el CSV antes de ejecutar.")
        
