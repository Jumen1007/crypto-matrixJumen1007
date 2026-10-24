import html
import re
import statistics
import time
import requests
import streamlit as st

st.set_page_config(
    page_title="Crypto Sentiment Matrix",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed",
)

TOKENS = {
    "BTC": {"cg": "bitcoin", "lc": "bitcoin", "llama_chain": "Bitcoin", "color": "orange"},
    "SOL": {"cg": "solana", "lc": "solana", "llama_chain": "Solana", "color": "purple"},
}
TIMEOUT = 5
WHALE_THRESHOLD_USD = 500000
STALE_SECONDS = 900

TECH_KEYWORDS = ["rsi", "order block", "order blocks", "divergencia", "divergence", 
                 "fibonacci", "fib", "macd", "soporte", "resistencia", "support", 
                 "resistance", "liquidity", "liquidez"]

BULL_WORDS = ["alcista", "bullish", "long", "compra", "buy", "breakout", "rebote", 
              "soporte", "acumul", "sube", "rompe al alza", "higher low"]

BEAR_WORDS = ["bajista", "bearish", "short", "venta", "sell", "breakdown", "caída", 
              "cae", "resistencia", "distribu", "lower high", "rechazo"]

def safe_get(url, params=None, headers=None):
    try:
        r = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None

def fmt_usd(x):
    if x >= 1e9:
        return f"${x/1e9:.2f}B"
    if x >= 1e6:
        return f"${x/1e6:.1f}M"
    return f"${x:,.0f}"

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
                continue
            price = float(d["usd"])
            chg = float(d["usd_24h_change"])
            vol = float(d["usd_24h_vol"])
            
            if chg > 5:
                mood = "Eufórico"
            elif chg < -5:
                mood = "Miedo"
            else:
                mood = "Neutral"
            out[sym] = {"price": price, "chg": chg, "vol": vol, "mood": mood}
        except Exception:
            continue
    return out

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

st.title("📊 Crypto Sentiment Matrix")
st.caption("BTC · SOL — 4 zonas de sentimiento")

if st.button("🔄 Actualizar", use_container_width=True):
    st.cache_data.clear()

retail = get_retail()

for sym, t in TOKENS.items():
    st.subheader(f"{sym}")
    r = retail.get(sym)
    if r:
        st.metric(label="Precio USD", value=f"${r['price']:,.2f}", delta=f"{r['chg']:.2f}%")
        st.write(f"**Retail:** {r['mood']} · Vol: {fmt_usd(r['vol'])}")
    
    w = get_whales(t["cg"], t["llama_chain"])
    if w.get("label"):
        st.write(f"**🐋 Ballenas:** {w['label']} (Vol x{w['ratio']:.2f})")
    if w.get("tvl_chg") is not None:
        st.write(f"**TVL On-chain:** {fmt_usd(w['tvl'])} ({w['tvl_chg']:+.2f}%)")
    st.divider()

st.header("🧠 Zona Expertos")
grok_text = st.text_area(
    "Entrada de Datos de Grok",
    key="grok_text",
    height=160,
    placeholder="Pega aquí el análisis de los traders...",
)

if grok_text.strip():
    items, bu, be = analyze_experts(grok_text)
    total = len(items)
    if total:
        bias = "Alcista" if bu > be else "Bajista" if be > bu else "Neutral"
        st.write(f"**Consenso:** {bias} ({bu} alcistas / {be} bajistas)")
        for text, tag in items:
            prefix = "🟢" if tag == "b" else "🔴" if tag == "s" else "⚪"
            st.info(f"{prefix} {text}")
        
