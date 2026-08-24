#!/usr/bin/env python3
"""
啟動 Ngrok Tunnel (port 5173) 並生成 QR Code
支援：Authtoken + 固定子網域（需付費方案）或隨機子網域（免費方案）
用法：python start_tunnel.py
"""
import subprocess
import time
import requests
import qrcode
from pathlib import Path

# ============ 設定區 ============
LOCAL_PORT = 5173
PROJECT_DIR = Path(__file__).parent
QR_OUTPUT = PROJECT_DIR / "tunnel_qrcode.png"

# 👇 修改這裡：若有付費方案可設定固定子網域（如 "print-factory"）
# 免費方案請設為 None，會自動產生隨機子網域
FIXED_SUBDOMAIN = None  # 例："print-factory" → https://print-factory.ngrok-free.app
# ================================

def get_ngrok_url():
    """從 Ngrok API 取得公開網址"""
    try:
        resp = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=3)
        tunnels = resp.json()["tunnels"]
        for t in tunnels:
            if t["config"]["addr"] == f"http://localhost:{LOCAL_PORT}":
                return t["public_url"]
    except Exception:
        pass
    return None

def generate_qrcode(url: str, output_path: Path):
    """生成 QR Code 圖片"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)
    print(f"✅ QR Code 已儲存：{output_path}")

def print_ascii_qr(url: str):
    """終端機顯示 ASCII QR Code"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=2,
        border=1,
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr.print_ascii(invert=True)
    print(f"\n公開網址：{url}\n")

def main():
    print(f"🚀 啟動 Ngrok Tunnel → http://localhost:{LOCAL_PORT}")
    
    # 建立 ngrok 指令 - 免費版無法完全關閉瀏覽器警告
    # 嘗試使用 --host-header=rewrite 減少警告出現機率
    cmd = ["ngrok", "http", str(LOCAL_PORT), "--host-header=rewrite"]
    if FIXED_SUBDOMAIN:
        cmd.extend(["--domain", f"{FIXED_SUBDOMAIN}.ngrok-free.app"])
        print(f"🔗 使用固定子網域：{FIXED_SUBDOMAIN}.ngrok-free.app")
    else:
        print("🎲 使用隨機子網域（免費方案）")
    
    # 1. 啟動 ngrok (背景)
    ngrok_proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    
    try:
        # 2. 等待 ngrok 就緒
        print("⏳ 等待 Ngrok 就緒...")
        for _ in range(20):
            time.sleep(1)
            public_url = get_ngrok_url()
            if public_url:
                break
        else:
            print("❌ Ngrok 啟動逾時，請檢查：")
            print("   1. Authtoken 是否已設定：ngrok config add-authtoken YOUR_TOKEN")
            print("   2. Port 5173 是否有 Vite 服務運行")
            print("   3. 固定子網域是否已在 Dashboard 宣告（付費方案）")
            print("   4. 嘗試手動執行：ngrok http 5173 --host-header=rewrite")
            return
        
        # 3. 確保是 https
        if public_url.startswith("http://"):
            public_url = public_url.replace("http://", "https://")
        
        print(f"✅ 公開網址：{public_url}")
        
        # 4. 生成 QR Code
        generate_qrcode(public_url, QR_OUTPUT)
        print_ascii_qr(public_url)
        
        print("📱 手機掃碼即可測試前端介面")
        print("⚠️ 免費版會出現 ngrok 警告頁面，點擊「Visit Site」即可進入")
        print("💡 付費方案可設定固定域名並完全關閉警告頁面")
        print("🛑 按 Ctrl+C 結束 Tunnel")
        
        # 5. 保持執行
        ngrok_proc.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 關閉 Tunnel...")
    finally:
        ngrok_proc.terminate()

if __name__ == "__main__":
    # 檢查依賴
    try:
        import qrcode
    except ImportError:
        print("📦 安裝 qrcode 套件...")
        subprocess.run(["pip", "install", "qrcode[pill]"], check=True)
        import qrcode
    
    main()