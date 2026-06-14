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
str_web.title("🎯 Benim Özel Solana Avcı Terminalim (Solana Core v2)")
str_web.caption("Sıfır Bulut Engeli - Raydium CPMM & AMM Canlı Havuz Yakalayıcı")

# --- ⚙️ SOL MENÜ: KİŞİSEL FİLTRELERİNİZ ---
str_web.sidebar.header("🛡️ Canlı Av Filtreleri")
BUY_AMOUNT_SOL = str_web.sidebar.number_input("Alım Miktarı (SOL)", min_value=0.005, value=0.01, step=0.005)
min_liq_usd = str_web.sidebar.number_input("Minimum Güvenli Likidite ($)", value=1500, step=500)

RAYDIUM_PROGRAM_ID = "675kPX9M4SG31g95s899vVn72p6w4fdfp4n75a8Jtxb7"
WSS_URL = os.getenv("HELIUS_WSS_URL")

if "my_working_data" not in str_web.session_state:
    str_web.session_state.my_working_data = []

def get_token_details_safely(token_address):
    """Yakaladığımız ham token adresini açık API üzerinden saniyeler içinde çözümler"""
    try:
        url = f"https://dexscreener.com{token_address}"
        res = std_requests.get(url, timeout=5).json()
        pairs = res.get("pairs", [])
        if not pairs: return None
        
        main_pair = pairs[0] if isinstance(pairs, list) else pairs
        liquidity_usd = float(main_pair.get("liquidity", {}).get("usd", 0))
        volume = main_pair.get("volume", {})
        info = main_pair.get("info", {})
        
        has_socials = "✅ AKTİF" if (len(info.get("socials", [])) > 0 or len(info.get("websites", [])) > 0) else "❌ YOK"
        
        if liquidity_usd >= min_liq_usd:
            return {
                "Coin Adı": main_pair.get("baseToken", {}).get("name", "Yeni Token"),
                "Sembol": main_pair.get("baseToken", {}).get("symbol", "TOKEN").upper(),
                "Kontrat Adresi (Mint)": token_address,
                "Likidite ($)": liquidity_usd,
                "5m Hacim ($)": float(volume.get("m5", 0)),
                "1H Hacim ($)": float(volume.get("h1", 0)),
                "Sosyal Medya": has_socials,
                "Anlık Fiyat ($)": float(main_pair.get("priceUsd", 0)) if main_pair.get("priceUsd") else 0.0
            }
    except:
        return None
    return None

async def start_helius_v2_listener():
    """Yeni nesil Solana havuz fonksiyonlarını ayrım yapmaksızın canlı yakalar"""
    subscribe_message = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "logsSubscribe",
        "params": [
            {"mentions": [RAYDIUM_PROGRAM_ID]},
            {"commitment": "processed"} # En yüksek veri hızı
        ]
    }
    
    async for websocket in connect(WSS_URL):
        try:
            await websocket.send(json.dumps(subscribe_message))
            await websocket.recv()
            
            async for message in websocket:
                data = json.loads(message)
                if "params" in data:
                    result = data["params"]["result"]["value"]
                    logs = str(result.get("logs", []))
                    
                    # 🌟 YENİ NESİL ÇÖZÜM: Sadece initialize2 değil, tüm havuz açılış kelimelerini tara
                    is_pool_creation = any(keyword in logs for keyword in ["initialize2", "initialize", "create_pool", "init_pool", "swapBaseIn"])
                    
                    if is_pool_creation:
                        # İşlemin içindeki potansiyel cüzdan adreslerini veya tokenları taramak için imzayı süzüyoruz
                        signature = result.get("signature")
                        if signature:
                            # Jupiter/DexScreener entegrasyonuyla token detaylarını çek
                            stats = get_token_details_safely(signature)
                            if stats and stats not in str_web.session_state.my_working_data:
                                str_web.session_state.my_working_data.append(stats)
        except:
            await asyncio.sleep(1)

# Arka plan iş parçacığı motoru
if "engine_running_v2" not in str_web.session_state:
    str_web.session_state.engine_running_v2 = True
    def run_engine():
        asyncio.run(start_helius_v2_listener())
    threading.Thread(target=run_engine, daemon=True).start()

# --- PANEL ARAYÜZÜ ---
if str_web.button("🔄 Paneli Canlı Yenile / Güncelle", type="primary"):
    str_web.rerun()

if str_web.session_state.my_working_data:
    df = pd.DataFrame(str_web.session_state.my_working_data).drop_duplicates(subset=["Kontrat Adresi (Mint)"])
    str_web.success(f"🔥 Canlı Solana Otobanından {len(df)} adet taze havuz başarıyla yakalandı!")
    str_web.dataframe(df, use_container_width=True)
else:
    str_web.info("📡 Yeni Nesil Solana Havuz Otobanına Bağlanıldı. Kriterlerinize uyan taze coin akışı bekleniyor...")

time.sleep(60)
str_web.rerun()
