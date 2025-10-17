import time
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime
from typing import List

# ---------------------------------------
# CONFIGURASI DASHBOARD
# ---------------------------------------
st.set_page_config(
    page_title="💰 Crypto Live Dashboard | CoinGecko",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("💰 Crypto Live Dashboard")
st.caption("📊 Real-time data dari [CoinGecko API](https://www.coingecko.com/en/api) — update otomatis setiap interval tertentu.")

# ---------------------------------------
# SIDEBAR PENGATURAN
# ---------------------------------------
with st.sidebar:
    st.header("⚙️ Pengaturan")
    coins_input = st.text_input(
        "Masukkan Coin IDs (pisahkan dengan koma)", 
        "bitcoin,ethereum,solana"
    )
    coins = [c.strip().lower() for c in coins_input.split(",") if c.strip()]
    vs_currency = st.selectbox("Mata Uang", ["usd", "idr", "eur", "btc"], index=0)
    interval = st.slider("Interval Update (detik)", 20, 120, 45, step=5)
    show_chart = st.checkbox("Tampilkan grafik harga", True)
    chart_days = st.selectbox("Rentang waktu grafik (hari)", [1, 7, 14, 30], index=0)

    st.divider()
    st.info("💡 Gunakan Coin ID sesuai CoinGecko, contoh: `bitcoin`, `ethereum`, `dogecoin`.")

# ---------------------------------------
# ⚙️ UTILITAS
# ---------------------------------------
@st.cache_data(ttl=60)
def ping_api() -> float:
    """Cek konektivitas ke API CoinGecko"""
    start = time.time()
    try:
        r = requests.get("https://api.coingecko.com/api/v3/ping", timeout=30)
        r.raise_for_status()
        return time.time() - start
    except requests.RequestException:
        return -1

@st.cache_data(ttl=30)
def fetch_market_data(vs_currency: str, coins: List[str]) -> pd.DataFrame:
    """Ambil data pasar koin"""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": vs_currency,
        "ids": ",".join(coins),
        "price_change_percentage": "1h,24h,7d",
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return pd.DataFrame(r.json())

@st.cache_data(ttl=120)
def fetch_market_chart(coin_id: str, vs_currency: str, days: int = 1) -> pd.DataFrame:
    """Ambil data historis harga untuk grafik"""
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": vs_currency, "days": days}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        prices = r.json().get("prices", [])
        df = pd.DataFrame(prices, columns=["timestamp_ms", "price"])
        df["timestamp"] = pd.to_datetime(df["timestamp_ms"], unit="ms")
        return df
    except Exception:
        return pd.DataFrame(columns=["timestamp", "price"])

# ---------------------------------------
# HELPER STYLING
# ---------------------------------------
def color_delta(val):
    if pd.isna(val):
        return ""
    color = "green" if val > 0 else "red"
    return f"color: {color}; font-weight: bold;"

# ---------------------------------------
# STATUS API
# ---------------------------------------
ping_time = ping_api()
if ping_time < 0:
    st.error("🚨 Tidak bisa terhubung ke CoinGecko API.")
else:
    st.success(f"✅ API aktif ({ping_time:.2f}s)")

# ---------------------------------------
# AMBIL DATA PASAR
# ---------------------------------------
try:
    df = fetch_market_data(vs_currency, coins)
except Exception as e:
    st.error(f"Gagal mengambil data dari API: {e}")
    st.stop()

if df.empty:
    st.warning("⚠️ Tidak ada data ditemukan. Periksa ID coin dan koneksi internet.")
    st.stop()

# ---------------------------------------
# PILIH KOLOM
# ---------------------------------------
columns_display = [
    "symbol", "name", "current_price", 
    "price_change_percentage_1h_in_currency",
    "price_change_percentage_24h_in_currency",
    "price_change_percentage_7d_in_currency",
    "high_24h", "low_24h", "ath",
    "market_cap", "total_volume",
    "market_cap_rank", "fully_diluted_valuation",
    "last_updated"
]

df_display = df[columns_display].copy()
df_display.rename(columns={
    "symbol": "Symbol",
    "name": "Coin",
    "current_price": f"Price ({vs_currency.upper()})",
    "price_change_percentage_1h_in_currency": "1H %",
    "price_change_percentage_24h_in_currency": "24H %",
    "price_change_percentage_7d_in_currency": "7D %",
    "high_24h": "24H High",
    "low_24h": "24H Low",
    "ath": "All Time High",
    "market_cap": "Market Cap",
    "total_volume": "Volume 24H",
    "market_cap_rank": "Rank",
    "fully_diluted_valuation": "FDV",
    "last_updated": "Last Update"
}, inplace=True)

# ---------------------------------------
# RINGKASAN METRIC CARD
# ---------------------------------------
st.subheader("📊 Ringkasan Harga")
cols = st.columns(min(len(df), 4))
for i, (_, r) in enumerate(df.iterrows()):
    with cols[i % len(cols)]:
        delta_24h = r["price_change_percentage_24h_in_currency"]
        st.metric(
            label=f"{r['name']} ({r['symbol'].upper()})",
            value=f"{r['current_price']:,} {vs_currency.upper()}",
            delta=f"{delta_24h:.2f}%" if pd.notna(delta_24h) else "—",
        )

# ---------------------------------------
# TABEL DETAIL
# ---------------------------------------
st.markdown("### 📋 Detail Pasar")
st.dataframe(
    df_display.style.format({
        f"Price ({vs_currency.upper()})": "{:,.4f}",
        "1H %": "{:.2f}",
        "24H %": "{:.2f}",
        "7D %": "{:.2f}",
        "24H High": "{:,.4f}",
        "24H Low": "{:,.4f}",
        "All Time High": "{:,.4f}",
        "Market Cap": "{:,.0f}",
        "Volume 24H": "{:,.0f}",
        "FDV": "{:,.0f}",
    }).applymap(color_delta, subset=["1H %", "24H %", "7D %"]),
    use_container_width=True,
    height=520,
)

# ---------------------------------------
# GRAFIK HARGA
# ---------------------------------------
if show_chart:
    st.markdown("### 📈 Grafik Harga")
    for coin in coins:
        data = fetch_market_chart(coin, vs_currency, chart_days)
        if data.empty:
            st.warning(f"Tidak ada data grafik untuk {coin}.")
            continue
        fig = px.line(
            data, x="timestamp", y="price",
            title=f"{coin.upper()} ({vs_currency.upper()}) - {chart_days} Hari",
            height=300
        )
        fig.update_layout(margin=dict(l=20, r=20, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------
# AUTO REFRESH (Fallback Aman)
# ---------------------------------------
st.divider()
st.info(f"🔄 Dashboard akan memperbarui otomatis setiap {interval} detik.")

progress = st.progress(0)
for i in range(interval):
    progress.progress((i + 1) / interval)
    time.sleep(1)

# Fallback untuk versi lama dan baru
try:
    st.experimental_rerun()  # Akan dipakai jika masih ada di versi lama
except AttributeError:
    st.rerun()  # Dipakai di Streamlit versi baru


