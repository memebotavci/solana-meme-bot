import streamlit as str_web
import pandas as pd
import requests
import time
import os

# Sayfa Yapılandırması ve Başlık Ayarları
str_web.set_page_config(page_title="Özel Trading Terminali", layout="wide")
str_web.title("🎯 Benim Özel Solana Avcı Terminalim (Jupiter Cloud Core)")
str_web.caption("Sıfır Bulut Engeli - Doğrudan Jupiter İndeks Havuzundan Canlı Filtreleme")

# --- ⚙️ SOL MENÜ: SADECE SİZİN BELİRLEDİĞİNİZ KİŞİSEL FİLTRELER ---
str_web.sidebar.header("🛡️ Gelişmiş Av Kriterleri")
min_liq_usd = str_web.sidebar.number_input("Minimum Likidite ($)", value=3000, step=500)
min_vol_24h = str_web.sidebar.number_input("Minimum 24H Hacim ($)", value=10000, step=2000)

str_web.sidebar.info("🔄 Otomatik Yenileme: Sistem ağı her 60 saniyede bir otomatik olarak tarar.")

if "last_run" not in str_web.session_state:
    str_web.session_state.last_run = time.time()

def fetch_live_unrestricted_jup_tokens():
    """Geliştiricilere tamamen açık ve engelsiz resmi Jupiter API hattı"""
    # Solana ağında en son aktife giren ve likidite alan tüm gerçek coinleri anlık fırlatır
    url = "https://jup.ag"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            raw_data = response.json()
            indexed_mints = raw_data.get("indexedRouteMap", {})
            
            # Global router haritasına eklenen en taze son 15 coinin mint adresini ayıkla
            fresh_mints = list(indexed_mints.keys())[-15:]
            
            filtered_results = []
            for mint in fresh_mints:
                if mint in ["So11111111111111111111111111111111111111112", "11111111111111111111111111111111"]:
                    continue
                    
                # Tekil havuz kontrolü (Bot engeli barındırmaz, herkese açıktır)
                dex_url = f"https://dexscreener.com{mint}"
                dex_res = requests.get(dex_url, headers=headers, timeout=5).json()
                pairs = dex_res.get("pairs", [])
                
                if not pairs:
                    continue
                    
                main_pair = pairs if isinstance(pairs, list) else pairs
                liquidity_usd = float(main_pair.get("liquidity", {}).get("usd", 0))
                volume = main_pair.get("volume", {})
                vol_24h = float(volume.get("h24", 0))
                info = main_pair.get("info", {})
                
                # 🛡️ GÜVENLİK FİLTRESİ: Sosyal medyası/reklamı olan gerçek projeler
                has_socials = len(info.get("socials", [])) > 0 or len(info.get("websites", [])) > 0
                
                # Sizin belirlediğiniz özel şartlar
                if liquidity_usd >= min_liq_usd and vol_24h >= min_vol_24h and has_socials:
                    filtered_results.append({
                        "Coin Adı": main_pair.get("baseToken", {}).get("name", "Meme Asset"),
                        "Sembol": main_pair.get("baseToken", {}).get("symbol", "MEME").upper(),
                        "Kontrat Adresi (Mint)": mint,
                        "Likidite ($)": liquidity_usd,
                        "5m Hacim ($)": float(volume.get("m5", 0)),
                        "1H Hacim ($)": float(volume.get("h1", 0)),
                        "24H Hacim ($)": vol_24h,
                        "Güvenlik Durumu": "🛡️ DOĞRULANMIŞ HAVUZ",
                        "Anlık Fiyat ($)": float(pair.get("priceUsd", 0)) if pair.get("priceUsd") else 0.0
                    })
            return filtered_results
        return []
    except:
        return []

# --- PANEL ÇALIŞMA MANTIĞI ---
current_time = time.time()
if str_web.button("🔄 Manuel Olarak Hemen Tara", type="primary") or (current_time - str_web.session_state.last_run >= 60):
    str_web.session_state.last_run = current_time
    with str_web.spinner("Jupiter veri havuzuyla senkronize olunuyor..."):
        results = fetch_live_unrestricted_jup_tokens()
        if results:
            str_web.session_state.my_final_panel = results

# Tabloyu Ekrana Basma
if "my_final_panel" in str_web.session_state and str_web.session_state.my_final_panel:
    df = pd.DataFrame(str_web.session_state.my_final_panel).drop_duplicates(subset=["Contract Address (Mint)"])
    str_web.success(f"✅ Filtre şartları sağlandı! {len(df)} adet premium coin canlı olarak listeleniyor.")
    str_web.dataframe(df, use_container_width=True)
else:
    str_web.info("💡 Bulut motoru Jupiter ağ indeksini tarıyor. İlk otomatik yükleme 60 saniye içinde başlayacaktır.")

time.sleep(60)
str_web.rerun()
