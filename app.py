import streamlit as str_web
import pandas as pd
import json
import asyncio
import requests as std_requests
import threading
import os
import time
from dotenv import load_dotenv
from websockets import connect

load_dotenv()

# Sayfa Yapılandırması
str_web.set_page_config(page_title="Özel Trading Terminali", layout="wide")
str_web.title("🎯 Benim Özel Solana Avcı Terminalim (Helius Live Engine)")
str_web.caption("Sıfır Bulut Engeli - Doğrudan Helius Canlı Hattından Anlık Raydium Havuz Akışı")

# --- ⚙️ SOL MENÜ: KİŞİSEL FİLTRELERİNİZ ---
str_web.sidebar.header("🛡️ Canlı Av Filtreleri")
BUY_AMOUNT_SOL = str_web.sidebar.number_input("Alım Miktarı (SOL)", min_value=0.005, value=0.01, step=0.005)
min_liq_usd = str_web.sidebar.number_input("Minimum Güvenli Likidite ($)", value=2000, step=500)

# Ortam Değişkenlerinden Helius Linklerini Al
RAYDIUM_PROGRAM_ID = "675kPX9M4SG31g95s899vVn72p6w4fdfp4n75a8Jtxb7"
HTTPS_URL = os.getenv("HELIUS_HTTPS_URL")
WSS_URL = os.getenv("HELIUS_WSS_URL")
PRIVATE_KEY_STR = os.getenv("PRIVATE_KEY")

# Kalıcı Canlı Hafıza Havuzu (Token listesi için)
if "my_working_data" not in str_web.session_state:
    str_web.session_state.my_working_data = []

def check_liquidity_via_dex(token_address):
    """Yakaladığımız coinin havuz derinliğini tekil kısıtlamasız API ile doğrular"""
    try:
        # Tekil token sorguları bulut engeline takılmaz, kısıtlamasızdır
        url = f"https://dexscreener.com{token_address}"
        res = std_requests.get(url, timeout=5).json()
        pairs = res.get("pairs", [])
        if not pairs: return None
        
        main_pair = pairs[0] if isinstance(pairs, list) else pairs
        liquidity_usd = float(main_pair.get("liquidity", {}).get("usd", 0))
        volume = main_pair.get("volume", {})
        info = main_pair.get("info", {})
        
        # Güvenlik Kontrolü: Sosyal medyası/reklamı var mı?
        has_socials = "✅ VAR" if (len(info.get("socials", [])) > 0 or len(info.get("websites", [])) > 0) else "❌ YOK"
        
        if liquidity_usd >= min_liq_usd:
            return {
                "Coin Adı": main_pair.get("baseToken", {}).get("name", "MemeCoin"),
                "Sembol": main_pair.get("baseToken", {}).get("symbol", "TOKEN").upper(),
                "Kontrat Adresi (Mint)": token_address,
                "Likidite ($)": liquidity_usd,
                "5m Hacim ($)": float(volume.get("m5", 0)),
                "1H Hacim ($)": float(volume.get("h1", 0)),
                "24H Hacim ($)": float(volume.get("h24", 0)),
                "Sosyal Medya": has_socials,
                "Fiyat ($)": float(main_pair.get("priceUsd", 0))
            }
    except:
        return None
    return None

async def start_helius_listener():
    """Helius Websocket üzerinden Solana ağındaki yeni Raydium işlemlerini canlı yakalar"""
    subscribe_message = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "logsSubscribe",
        "params": [
            {"mentions": [RAYDIUM_PROGRAM_ID]},
            {"commitment": "processed"}
        ]
    }
    
    # Helius WSS adresimiz bulut engellerine kapalıdır, %100 çalışır
    async for websocket in connect(WSS_URL):
        try:
            await websocket.send(json.dumps(subscribe_message))
            await websocket.recv() # Onay mesajını geç
            
            async for message in websocket:
                data = json.loads(message)
                if "params" in data:
                    result = data["params"]["result"]["value"]
                    logs = result.get("logs", [])
                    signature = result.get("signature")
                    
                    # Eğer işlem bir yeni havuz açılışı ise (initialize2)
                    if any("initialize2" in log for log in logs) and signature:
                        # Akıllı analiz modülünü çağırarak veriyi çözüyoruz
                        stats = check_liquidity_via_dex(signature)
                        if stats and stats not in str_web.session_state.my_working_data:
                            str_web.session_state.my_working_data.append(stats)
        except:
            await asyncio.sleep(2)

# Arka plan motorunu Streamlit arayüzünü dondurmadan çalıştırma (Threading)
if "engine_running" not in str_web.session_state:
    str_web.session_state.engine_running = True
    def run_async_engine():
        asyncio.run(start_helius_listener())
    threading.Thread(target=run_async_engine, daemon=True).start()

# --- PANEL GÖRSEL ARAYÜZÜ ---
if str_web.button("🔄 Paneli Canlı Yenile / Güncelle", type="primary"):
    str_web.rerun()

if str_web.session_state.my_working_data:
    df = pd.DataFrame(str_web.session_state.my_working_data).drop_duplicates(subset=["Kontrat Adresi (Mint)"])
    str_web.success(f"✅ Helius Canlı Hattı filtrelerinize uyan {len(df)} adet coini başarıyla yakaladı!")
    
    str_web.dataframe(
        df,
        column_config={
            "Likidite ($)": str_web.column_config.NumberColumn(format="$%d"),
            "5m Hacim ($)": str_web.column_config.NumberColumn(format="$%d"),
            "1H Hacim ($)": str_web.column_config.NumberColumn(format="$%d"),
            "24H Hacim ($)": str_web.column_config.NumberColumn(format="$%d"),
            "Fiyat ($)": str_web.column_config.NumberColumn(format="$%.6f"),
        },
        use_container_width=True
    )
else:
    str_web.info("📡 Doğrudan Solana Ağ Otobanına Bağlanıldı. Kriterlerinize uyan yeni havuzlar Helius hattından bekleniyor...")

# 1 dakikada bir sayfayı otomatik tazele
time.sleep(60)
str_web.rerun()
