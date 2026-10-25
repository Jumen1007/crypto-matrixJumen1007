import streamlit as st

def render_zona_expertos():
    st.markdown("---")
    st.markdown("## 🧠 Zona Expertos (Últimas 12h)")
    st.caption("Filtro analítico: Coinglass, Arkham Intelligence y CryptoQuant")

    # --- DATOS DUROS EXTRACTADOS DE GROK ---
    BTC_LIQ = "Masiva dominancia long ($404M de $436M en 4h; ~92.6%); cascada tras ruptura <$80k (low ~$79.280). Heatmaps activan liquidez densa $79.4k–$79.5k (down) y $82.2k (up)."
    BTC_FLOWS = "Transferencia on-chain récord 2026 (>230k BTC / >$21B) entre wallets privadas (no exchanges). Hashrate en alza y mineros a plena capacidad. ETF spot semanal neto +5.183 BTC."
    BTC_RANGES = "**Soporte inmediato:** $79.4k–$80.1k | **Resistencia clave:** $82.2k–$85k"

    SOL_OI = "OI estable ~$3.38B (+0.4% 24h); funding positivo (+0.0055%–0.01% 8h, longs pagan). Liquidaciones 24h ~$18–23.5M (86–87% longs)."
    SOL_FLOWS = "Sin actividad institucional o de ballenas de alto impacto detectada en la ventana filtrada por Arkham."
    SOL_RANGES = "**Soporte inmediato:** ~$100 | **Resistencia clave:** No consensuada (~$102 post-caída)"

    SINTESIS_MATRICIAL = "Sesgo institucional de acumulación lateral post-flush de longs: BTC absorbe liquidaciones y mantiene estructura sobre $79–80k con hashrate/ETF positivos, mientras SOL muestra leve sesgo long residual sin flujos on-chain relevantes."

    # --- RENDERIZADO EN INTERFAZ MÓVIL ---
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

# Elimina el numeral (#) de abajo si quieres que se ejecute inmediatamente al final de tu app.py
render_zona_expertos()
