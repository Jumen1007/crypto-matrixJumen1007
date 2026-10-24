Crypto Sentiment Matrix - BTC & SOL
Streamlit app, mobile-first, dark theme, fallo silencioso.
requirements.txt:
streamlit
requests
Opcional (Streamlit Cloud > Settings > Secrets):
LUNARCRUSH_API_KEY = "tu_clave"
"""
import html
import re
import statistics
import time
import requests
import streamlit as st

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Crypto Sentiment Matrix",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed",
)

TOKENS = {
    "BTC": {"cg": "bitcoin", "lc": "bitcoin", "llama_chain": "Bitcoin", "color": "#F7931A"},
    "SOL": {"cg": "solana", "lc": "solana", "llama_chain": "Solana", "color": "#9945FF"},
}
TIMEOUT = 5
WHALE_THRESHOLD_USD = 500_000
STALE_SECONDS = 15 * 60

TECH_KEYWORDS = ["rsi", "order block", "order blocks", "divergencia", "divergence", 
                 "fibonacci", "fib", "macd", "soporte", "resistencia", "support", 
                 "resistance", "liquidity", "liquidez"]

BULL_WORDS = ["alcista", "bullish", "long", "compra", "buy", "breakout", "rebote", 
              "soporte", "acumul", "sube", "rompe al alza", "higher low"]

BEAR_WORDS = ["bajista", "bearish", "short", "venta", "sell", "breakdown", "caída", 
              "cae", "resistencia", "distribu", "lower high", "rechazo"]

# ----------------------------------------------------------------------------
# ESTILO (tema oscuro + tarjetas)
# ----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {background:#0b0e14; color:#e6e8ee;}
    header[data-testid="stHeader"] {background:transparent;}
    .block-container {padding:1rem 0.8rem 3rem 0.8rem; max-width:560px;}
    h1 {font-size:1.35rem !important; text-align:center; margin-bottom:0.2rem;}
    .sub {text-align:center; color:#8b93a7; font-size:0.78rem; margin-bottom:0.8rem;}
    .card {background:#141a26; border:1px solid #232c3f; border-radius:14px; padding:12px 14px; margin-bottom:12px;}
    .card h3 {margin:0 0 6px 0; font-size:1.05rem;}
    .zone {border-top:1px solid #232c3f; padding-top:8px; margin-top:8px;}
    .zone .t {font-size:0.7rem; letter-spacing:.06em; color:#8b93a7; text-transform:uppercase;}
    .zone .l {font-size:0.88rem; line-height:1.35; margin:2px 0;}
    .up {color:#2ecc71; font-weight:600;} .down {color:#ff5c5c; font-weight:600;}
    .neu {color:#f1c40f; font-weight:600;} .muted {color:#8b93a7;}
    .expert {background:#101622; border-left:3px solid #3b4660; border-radius:8px; padding:8px 10px; margin:6px 0; font-size:0.85rem;}
    .expert.b {border-left-color:#2ecc71;} .expert.s {border-left-color:#ff5c5c;}
    textarea {background:#101622 !important; color:#e6e8ee !important;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# UTILIDADES DE RED (fallo silencioso)
# ----------------------------------------------------------------------------
def safe_get(url, params=None, headers=None):
    """GET con timeout estricto. Devuelve JSON o None. Nunca muestra errores."""
    try:
        r = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None

def cls_for(label):
    if label in ("Eufórico", "Alcista (Acumulación)", "Alcista"):
        return "up"
    if label in ("Miedo", "Bajista (Distribución)", "Bajista"):
        return "down"
    return "neu"

def fmt_usd(x):
    if x >= 1e9:
        return f"${x/1e9:.2f}B"
    if x >= 1e6:
        return f"${x/1e6:.1f}M"
    return f"${x:,.0f}"

# ----------------------------------------------------------------------------
# D) USUARIOS GENERALES - CoinGecko
# ----------------------------------------------------------------------------
@st.cache_data(ttl=60, show_spinner=False)
def get_retail():
    ids = ",".join(t["cg"] for t in TOKENS.values())
    data = safe_get(
        "https://coingecko.com",
        params={
            "ids": ids,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_last_updated_at": "true",
        },
    )
    out = {}
    if not data:
        return out
    now = time.time()
    for sym, t in TOKENS.items():
        d = data.get(t["cg"])
        try:
            if not d:
                continue
            if now - float(d.get("last_updated_at", 0)) > STALE_SECONDS:
                continue  # dato desactualizado -> se ignora en silencio
            price = float(d["usd"])
            chg = float(d["usd_24h_change"])
            vol = float(d["usd_24h_vol"])
            
            if chg > 5:
                mood = "Eufórico"
            elif chg < -5:
                mood = "Miedo"
            else:
                mood = "Neutral / Indiferente"
            out[sym] = {"price": price, "chg": chg, "vol": vol, "mood": mood}
        except Exception:
            continue
    return out

# ----------------------------------------------------------------------------
# A) BALLENAS - proxy de flujos con volumen CoinGecko + TVL DeFiLlama
# ----------------------------------------------------------------------------
@st.cache_data(ttl=300, show_spinner=False)
def get_whales(cg_id, llama_chain):
    res = {}
    mc = safe_get(
        f"https://coingecko.com{cg_id}/market_chart",
        params={"vs_currency": "usd", "days": "7"},
    )
    try:
        vols = [v[1] for v in mc["total_volumes"] if v and v[1]]
        prices = [p[1] for p in mc["prices"] if p and p[1]]
        if len(vols) > 24 and len(prices) > 24:
            current = vols[-1]
            baseline = statistics.median(vols[:-24])
            excess = current - baseline
            ratio = current / baseline if baseline else 0
            # dirección aproximada: precio hoy vs hace ~24h
            price_move = prices[-1] / prices[-24] - 1
            
            if excess > WHALE_THRESHOLD_USD and ratio >= 1.3:
                if price_move >= 0:
                    label = "Alcista (Acumulación)"
                else:
                    label = "Bajista (Distribución)"
            else:
                label = "Neutral"
            res.update({"label": label, "ratio": ratio, "excess": excess})
    except Exception:
        pass

    tvl = safe_get(f"https://llama.fi{llama_chain}")
    try:
        if tvl and len(tvl) > 2:
            last, prev = float(tvl[-1]["tvl"]), float(tvl[-2]["tvl"])
            if prev > 0:
                res["tvl_chg"] = (last / prev - 1) * 100
                res["tvl"] = last
    except Exception:
        pass
    return res

# ----------------------------------------------------------------------------
# C) NIVEL MEDIO - LunarCrush (requiere API key opcional)
# ----------------------------------------------------------------------------
@st.cache_data(ttl=300, show_spinner=False)
def get_midlevel(topic, api_key):
    if not api_key:
        return None
    data = safe_get(
        f"https://lunarcrush.com{topic}/posts/v1",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    try:
        posts = data["data"]
        total = len(posts)
        tech, sents = 0, []
        for p in posts:
            text = " ".join(str(p.get(k, "")) for k in ("post_title", "post_text", "text")).lower()
            if any(k in text for k in TECH_KEYWORDS):
                tech += 1
            s = p.get("post_sentiment")
            if s is not None:
                sents.append(float(s))  # escala 1-5
        if total == 0 or not sents:
            return None
        pos = sum(1 for s in sents if s >= 3.5)
        return {"pct": pos / len(sents) * 100, "tech": tech, "total": total}
    except Exception:
        return None

# ----------------------------------------------------------------------------
# B) EXPERTOS - texto de Grok
# ----------------------------------------------------------------------------
def analyze_experts(text):
    blocks = [b.strip() for b in re.split(r"\n\s*\n|\n(?=\s*(?:\d+[\.\)]|[-•@]))", text) if b.strip()]
    items, bull_n, bear_n = [], 0, 0
    for b in blocks[:10]:
        low = b.lower()
        bu = sum(w in low for w in BULL_WORDS)
        be = sum(w in low for w in BEAR_WORDS)
        tag = "b" if bu > be else "s" if be > bu else ""
        bull_n += tag == "b"
        bear_n += tag == "s"
        items.append((b, tag))
    return items, bull_n, bear_n

# ----------------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------------
st.markdown("# 📊 Crypto Sentiment Matrix")
st.markdown('<div class="sub">BTC · SOL — 4 zonas de sentimiento</div>', unsafe_allow_html=True)

if st.button("🔄 Actualizar", use_container_width=True):
    st.cache_data.clear()

retail = get_retail()
try:
    lc_key = st.secrets.get("LUNARCRUSH_API_KEY", "")
except Exception:
    lc_key = ""

for sym, t in TOKENS.items():
    parts = [f'<div class="card"><h3 style="color: {t["color"]}">{sym}']
    r = retail.get(sym)
    if r:
        arrow = "▲" if r["chg"] >= 0 else "▼"
        c = "up" if r["chg"] >= 0 else "down"
        parts.append(
            f' <span class="muted" style="font-size:.95rem">${r["price"]:,.2f}</span> '
            f'<span class="{c}" style="font-size:.85rem">{arrow} {r["chg"]:+.2f}%</span>'
        )
    parts.append("</h3>")
    
    # A) Ballenas
    w = get_whales(t["cg"], t["llama_chain"])
    lines = []
    if w.get("label"):
        lines.append(
            f'<div class="l"><span class="{cls_for(w["label"])}">{w["label"]}</span> '
Usa el código con precaución.
f'· vol ×{w["ratio"]:.2f} vs. normal ({fmt_usd(max(w["excess"], 0))} extra)'
)
if w.get("tvl_chg") is not None:
c = "up" if w["tvl_chg"] >= 0 else "down"
lines.append(
f'TVL on-chain: {fmt_usd(w["tvl"])} '
f'{w["tvl_chg"]:+.2f}% (24h)'
)
if lines:
parts.append('🐋 Ballenas' + "".join(lines) + "")
else:
parts.append('🐋 BallenasActualizando...')
# C) Nivel medio
mid = get_midlevel(t["lc"], lc_key)
if mid:
c = "up" if mid["pct"] >= 55 else "down" if mid["pct"] <= 45 else "neu"
parts.append(
'📈 Nivel medio (lenguaje técnico)'
f'{mid["pct"]:.0f}% positivo '
f'· {mid["tech"]} de {mid["total"]} posts técnicos'
)
# D) Retail
if r:
parts.append(
'👥 Retail'
f'<span class="{cls_for(r["mood"])}">{r["mood"]} '
f'· Vol 24h: {fmt_usd(r["vol"])}'
)
parts.append("")
st.markdown("".join(parts), unsafe_allow_html=True)

B) Expertos

st.markdown('🧠 Zona Expertos', unsafe_allow_html=True)
grok_text = st.text_area(
"Entrada de Datos de Grok",
key="grok_text",
height=160,
placeholder="Pega aquí el texto de los 5 analistas (un analista por párrafo o por línea)...",
)
if grok_text.strip():
items, bu, be = analyze_experts(grok_text)
total = len(items)
if total:
bias = "Alcista" if bu > be else "Bajista" if be > bu else "Neutral"
st.markdown(
f'Consenso: {bias} '
f'· {bu} alcistas / {be} bajistas de {total} ',
unsafe_allow_html=True,
)
for text, tag in items:
st.markdown(
f'{html.escape(text)}',
unsafe_allow_html=True,
)
st.markdown("", unsafe_allow_html=True)
st.markdown(
f'Actualizado {time.strftime("%H:%M:%S")} · No es consejo financiero',
unsafe_allow_html=True,
)
