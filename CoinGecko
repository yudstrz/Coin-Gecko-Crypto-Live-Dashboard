# app.py
import time
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime
from typing import List, Dict, Any

# ------------------------------
# Konfigurasi Aplikasi
# ------------------------------
st.set_page_config(
    page_title="💰 Crypto Live Dashboard | CoinGecko",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("💰 **Crypto Live Dashboard**")
st.caption("Data real-time dari [CoinGecko API](https://www.coingecko.com/en/api) — update otomatis setiap interval yang ditentukan.")

# ------------------------------
# Sidebar - Pengaturan
# ------------------------------
with st.sidebar:
    st.header("⚙️ Pengaturan")
    coin_input = st.text_input("Masukkan Coin IDs (pisahkan dengan koma)", "bitcoin,ethereum,solana,cardano")
    coins = [c.strip().lower() for c in coin_input.split(",") if c.strip()]

    vs_currency = st.selectbox("Mata Uang", ["usd", "idr", "eur", "btc"], index=0)
    interval = st.slider("Interval Update (detik)", 20, 120, 45, step=5)

    show_chart = st.checkbox("Tampilkan grafik harga 24 jam", True)
    chart_days = st.selectbox("Rentang Waktu Grafik (hari)", [1, 7, 14, 30], index=0)

    st.divider()
    st.info("💡 Tips: Gunakan ID Coin sesuai CoinGecko, contoh: `bitcoin`, `ethereum`, `dogecoin`.")

# ------------------------------
# Fungsi Utilitas
# ------------------------------
@st.cache_data(ttl=60)
def ping_api() -> float:
    """Ping CoinGecko API untuk mengukur respon"""
    start = time.time()
    try:
        r = requests.get("https://api.coingecko.com/api/v3/ping", timeout=5)
        r.raise_for_status()
        return time.time() - start
    except requests.RequestException:
        return -1

@st.cache_data(ttl=30)
def fetch_market_data(vs_currency: str, coin_list: List[str]) -> pd.DataFrame:
    """Ambil data pasar dari CoinGecko (lebih lengkap daripada simple/price)"""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": vs_currency, "ids": ",".join(coin_list), "price_change_percentage": "1h,24h,7d"}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    return pd.DataFrame(data)

@st.cache_data(ttl=120)
def fetch_market_chart(coin_id: str, vs_currency: str, days: int = 1) -> pd.DataFrame:
    """Ambil data historis harga untuk sparkline/chart"""
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

def color_delta(v):
    """Warna untuk perubahan harga"""
    if v is None or pd.isna(v):
        return "black"
    return "green" if v > 0 else "red"

# ------------------------------
# 🛰️ Status Koneksi API
# ------------------------------
ping_time = ping_api()
if ping_time < 0:
    st.error("🚨 Gagal terhubung ke API CoinGecko.")
else:
    st.success(f"✅ API aktif ({ping_time:.2f}s)")

# ------------------------------
# Ambil Data
# ------------------------------
try:
    df = fetch_market_data(vs_currency, coins)
except Exception as e:
    st.error(f"Gagal mengambil data dari CoinGecko: {e}")
    st.stop()

if df.empty:
    st.warning("Tidak ada data ditemukan. Periksa ID coin atau jaringan internet.")
    st.stop()

# ------------------------------
# Kolom yang Ditampilkan
# ------------------------------
columns_display = [
    "symbol", "name", "current_price", "price_change_percentage_1h_in_currency",
    "price_change_percentage_24h_in_currency", "price_change_percentage_7d_in_currency",
    "high_24h", "low_24h", "ath", "market_cap", "total_volume",
    "market_cap_rank", "fully_diluted_valuation", "last_updated"
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

# ------------------------------
# Tampilan Utama - Kartu Ringkas
# ------------------------------
st.subheader("📊 Ringkasan Harga Kripto")

cols = st.columns(min(len(df), 4))
for i, (_, r) in enumerate(df.iterrows()):
    with cols[i % len(cols)]:
        delta_24h = r["price_change_percentage_24h_in_currency"]
        st.metric(
            label=f"{r['name']} ({r['symbol'].upper()})",
            value=f"{r['current_price']:,} {vs_currency.upper()}",
            delta=f"{delta_24h:.2f}%" if pd.notna(delta_24h) else "—"
        )

# ------------------------------
# Tabel Data Detail
# ------------------------------
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
    height=500
)

# ------------------------------
# Grafik Sparkline per Coin
# ------------------------------
if show_chart:
    st.markdown("### 📈 Grafik Harga 24 Jam Terakhir")
    for coin in coins:
        mdf = fetch_market_chart(coin, vs_currency, days=chart_days)
        if mdf.empty:
            st.warning(f"⚠️ Tidak ada data grafik untuk {coin}.")
            continue
        fig = px.line(mdf, x="timestamp", y="price", title=f"{coin.upper()} ({vs_currency.upper()})", height=300)
        fig.update_layout(margin=dict(l=20, r=20, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

# ------------------------------
# Auto Refresh Progress
# ------------------------------
st.divider()
col1, col2 = st.columns([3, 1])
with col1:
    st.info(f"🔄 Dashboard akan memperbarui otomatis setiap {interval} detik.")
with col2:
    progress = st.progress(0)
    for i in range(interval):
        progress.progress((i + 1) / interval)
        time.sleep(1)
    st.experimental_rerun()
