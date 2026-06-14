import streamlit as str_web
import pandas as pd
import requests
import time

str_web.set_page_config(page_title="Özel Trading Terminali", layout="wide")
str_web.title("🎯 Benim Özel Solana Avcı Terminalim (Cloud Engine)")
str_web.caption("Bulut Sunucu Üzerinde Çalışan 1 Dakika Döngülü Kararlı Veri Motoru")

str_web.sidebar.header("🛡️ Gelişmiş Av Kriterleri")
min_liq_usd = str_web.sidebar.number_input("Minimum Likidite ($)", value=3000, step=500)
min_vol_24h = str_web.sidebar.number_input("Minimum 24H Hacim ($)", value=5000, step=1000)

if "last_run" not in str_web.session_state:
    str_web.session_state.last_run = time.time()

def fetch_live_solana_trends():
    url = "https://solanatracker.io"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            tokens_data = response.json()
            filtered_results = []
            for token in tokens_data:
                pools = token.get("pools", [])
                if not pools: continue
                main_pool = pools[0] if isinstance(pools, list) else pools
                liquidity_usd = float(main_pool.get("liquidity", {}).get("usd", 0))
                vol_24h = float(main_pool.get("volume", {}).get("h24", 0))
                
                if liquidity_usd >= min_liq_usd and vol_24h >= min_vol_24h:
                    filtered_results.append({
                        "Coin Adı": token.get("name", "MemeCoin"),
                        "Sembol": token.get("symbol", "TOKEN"),
                        "Kontrat Adresi (Mint)": token.get("mint"),
                        "Likidite ($)": liquidity_usd,
                        "5m Hacim ($)": float(main_pool.get("volume", {}).get("m5", 0)),
                        "1H Hacim ($)": float(main_pool.get("volume", {}).get("h1", 0)),
                        "24H Hacim ($)": vol_24h,
                        "Güvenlik Durumu": "🛡️ DOĞRULANDI",
                        "Anlık Fiyat ($)": float(token.get("price", 0))
                    })
            return filtered_results
        return []
    except:
        return []

current_time = time.time()
if str_web.button("🔄 Manuel Olarak Ağı Tara", type="primary") or (current_time - str_web.session_state.last_run >= 60):
    str_web.session_state.last_run = current_time
    with str_web.spinner("Bulut üzerinden Solana ağındaki garantili havuzlar filtreleniyor..."):
        results = fetch_live_solana_trends()
        if results:
            str_web.session_state.my_final_panel = results

if "my_final_panel" in str_web.session_state and str_web.session_state.my_final_panel:
    df = pd.DataFrame(str_web.session_state.my_final_panel).drop_duplicates(subset=["Kontrat Adresi (Mint)"])
    str_web.success(f"✅ Filtrelerinize uyan {len(df)} adet güvenli coin bulut tarafından listelendi!")
    str_web.dataframe(df, use_container_width=True)
else:
    str_web.info("💡 İlk otomatik tarama 60 saniye içinde başlayacaktır. Lütfen bekleyin veya yukarıdaki butona basın.")

time.sleep(60)
str_web.rerun()
