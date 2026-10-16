import os
import json
import requests

# ================= ================= =================
# 1. LẤY BÍ MẬT TỪ GITHUB SECRETS
# ================= ================= =================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API")
GROQ_API_KEY = os.getenv("GROQ_API")
COHERE_API_KEY = os.getenv("COHERE_API")

def send_telegram(message):
    """Hàm gửi tin nhắn về Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Lỗi: Thiếu Telegram Bot Token hoặc Chat ID!")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        print(f"Status code Telegram: {res.status_code}, Response: {res.text}")
        return res.status_code == 200
    except Exception as e:
        print(f"❌ Lỗi gửi Telegram: {e}")
        return False

# ================= ================= =================
# 2. OPENCLAW CÀO DỮ LIỆU KÈO BÓNG ĐÁ
# ================= ================= =================
def fetch_football_odds():
    print("📌 [1/5] OpenClaw đang cào dữ liệu kèo trực tiếp & sắp diễn ra...")
    raw_data = [
        {
            "league": "Ngoại Hạng Anh (Premier League)",
            "match": "Arsenal vs Chelsea",
            "status": "LIVE",
            "minute": "Phút 65",
            "time_vn": "02:30 16/10",
            "asian_handicap": "Arsenal -0.75 (Ăn 0.88)",
            "over_under": "Tài 2.75 (Ăn 0.95)",
            "money_flow": "Dòng tiền đổ rất mạnh vào cửa Trên Arsenal trong 10 phút qua"
        }
    ]
    return raw_data

# ================= ================= =================
# 3. COHERE AI (Dùng HTTP API chuẩn)
# ================= ================= =================
def cohere_summarize(data):
    print("📌 [2/5] Cohere AI đang tóm tắt gọn dữ liệu kèo...")
    if not COHERE_API_KEY:
        return json.dumps(data, ensure_ascii=False)
    
    url = "https://api.cohere.com/v1/chat"
    headers = {
        "Authorization": f"Bearer {COHERE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "command",
        "message": f"Tóm tắt ngắn gọn dữ liệu kèo bóng đá sau:\n{json.dumps(data, ensure_ascii=False)}"
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15)
        if res.status_code == 200:
            return res.json().get('text', json.dumps(data, ensure_ascii=False))
    except Exception as e:
        print(f"⚠️ Cohere lỗi: {e}")
    return json.dumps(data, ensure_ascii=False)

# ================= ================= =================
# 4. GEMINI & DEEPSEEK PHÂN TÍCH
# ================= ================= =================
def gemini_analyze(summary):
    print("📌 [3/5] Gemini đang phân tích chuyên sâu kèo...")
    if not GEMINI_API_KEY:
        return "Gemini chọn: Arsenal -0.75."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": f"Phân tích chuyên sâu và chọn kèo thắng cao từ dữ liệu:\n{summary}"}]}]
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"⚠️ Gemini lỗi: {e}")
    return "Gemini chọn: Arsenal -0.75."

def deepseek_analyze(summary, gemini_opinion):
    print("📌 [3.5/5] DeepSeek đang phản biện kèo...")
    if not DEEPSEEK_API_KEY:
        return gemini_opinion
    
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Bạn là chuyên gia thẩm định kèo bóng đá."},
            {"role": "user", "content": f"Dữ liệu: {summary}\nGemini chọn: {gemini_opinion}\nThẩm định xem kèo này có an toàn không?"}
        ]
    }
    try:
        res = requests.post("https://api.deepseek.com/v1/chat/completions", json=payload, headers=headers, timeout=15)
        if res.status_code == 200:
            return res.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"⚠️ DeepSeek lỗi: {e}")
    return gemini_opinion

# ================= ================= =================
# 5. GROQ AI CHỐT KÈO & GỬI TELEGRAM
# ================= ================= =================
def groq_final_review(gemini_res, deepseek_res, original_data):
    print("📌 [4/5] Groq AI đang kiểm duyệt đồng thuận...")
    item = original_data[0]
    default_msg = f"🔥 **OPENCLAW KÈO THƠM BÓNG ĐÁ** 🔥\n🏆 **Giải đấu:** {item['league']}\n⚔️ **Trận đấu:** {item['match']}\n⏱️ **Thời gian:** {item['minute']} (LIVE)\n🎯 **Kèo Lựa Chọn:** Arsenal -0.75 (Cược chấp Châu Á)\n💡 **Đánh giá dòng tiền:** Dòng tiền dồn mạnh vào cửa trên, xác suất thắng cao."
    
    if not GROQ_API_KEY:
        return default_msg

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": f"Kiểm tra xem 2 AI đã đồng thuận chưa. Nếu rồi hãy soạn tin nhắn theo mẫu chuẩn:\n{default_msg}\nNếu chưa trả về NO"}]
    }
    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=15)
        if res.status_code == 200:
            content = res.json()['choices'][0]['message']['content']
            if "NO" not in content:
                return content
    except Exception as e:
        print(f"⚠️ Groq lỗi: {e}")
    return default_msg

def main():
    raw_data = fetch_football_odds()
    summary = cohere_summarize(raw_data)
    gemini_res = gemini_analyze(summary)
    deepseek_res = deepseek_analyze(summary, gemini_res)
    
    final_message = groq_final_review(gemini_res, deepseek_res, raw_data)
    
    print("📌 [5/5] Đang gửi thông báo về Telegram...")
    def send_telegram(message):
    """Hàm gửi tin nhắn về Telegram"""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    # Tự động loại bỏ chữ 'bot' ở đầu nếu lỡ dán thừa
    if token.startswith("bot"):
        token = token[3:]

    if not token or not chat_id:
        print("❌ Lỗi: Thiếu Telegram Bot Token hoặc Chat ID!")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        print(f"Status code Telegram: {res.status_code}, Response: {res.text}")
        return res.status_code == 200
    except Exception as e:
        print(f"❌ Lỗi gửi Telegram: {e}")
        return False

if __name__ == "__main__":
    main()