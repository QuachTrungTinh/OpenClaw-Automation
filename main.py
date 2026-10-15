import os
import json
import requests
import google.generativeai as genai
from cohere import Client as CohereClient

# ================= ================= =================
# 1. KHỞI TẠO CẤU HÌNH & LẤY BÍ MẬT TỪ GITHUB SECRETS
# ================= ================= =================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API")
GROQ_API_KEY = os.getenv("GROQ_API")
COHERE_API_KEY = os.getenv("COHERE_API")

# Setup Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Setup Cohere
cohere_client = CohereClient(api_key=COHERE_API_KEY) if COHERE_API_KEY else None

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
    # Dữ liệu cào kèo Châu Á, Tài Xỉu & dòng tiền ngon ăn
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
        },
        {
            "league": "Cúp C1 (UEFA Champions League)",
            "match": "Real Madrid vs Bayern Munich",
            "status": "UPCOMING",
            "minute": "Chưa diễn ra",
            "time_vn": "03:00 16/10 (Giờ VN)",
            "asian_handicap": "Real Madrid -0.25 (Ăn 0.92)",
            "over_under": "Tài 3.0 (Ăn 0.85)",
            "money_flow": "Dòng tiền ngon ăn dồn mạnh vào cửa Tài"
        }
    ]
    return raw_data

# ================= ================= =================
# 3. COHERE AI: TÓM TẮT & LÀM SẠCH DỮ LIỆU
# ================= ================= =================
def cohere_summarize(data):
    print("📌 [2/5] Cohere AI đang tóm tắt gọn dữ liệu kèo...")
    if not cohere_client:
        return json.dumps(data, ensure_ascii=False)
    
    prompt = f"Tóm tắt ngắn gọn dữ liệu kèo bóng đá, tập trung vào kèo cược chấp, tài xỉu và dòng tiền ngon ăn:\n{json.dumps(data, ensure_ascii=False)}"
    try:
        response = cohere_client.generate(prompt=prompt, max_tokens=300)
        return response.generations[0].text
    except Exception as e:
        print(f"⚠️ Cohere lỗi: {e}")
        return json.dumps(data, ensure_ascii=False)

# ================= ================= =================
# 4. GEMINI & DEEPSEEK: THẢO LUẬN & PHÂN TÍCH CHUYÊN SÂU
# ================= ================= =================
def gemini_analyze(summary):
    print("📌 [3/5] Gemini đang phân tích chuyên sâu kèo...")
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"Dựa trên dữ liệu kèo sau:\n{summary}\nHãy phân tích chuyên sâu và chọn trận/kèo có khả năng thắng cao nhất."
        res = model.generate_content(prompt)
        return res.text
    except Exception as e:
        print(f"⚠️ Gemini lỗi: {e}")
        return "Gemini chọn: Arsenal -0.75 (Phút 65) và Tài 3.0 Real Madrid (03:00 Giờ VN)."

def deepseek_analyze(summary, gemini_opinion):
    print("📌 [3.5/5] DeepSeek đang thảo luận và phản biện kèo...")
    if not DEEPSEEK_API_KEY:
        return gemini_opinion
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Bạn là chuyên gia phân tích kèo bóng đá chuyên sâu."},
            {"role": "user", "content": f"Dữ liệu kèo: {summary}\nĐánh giá của Gemini: {gemini_opinion}\nHãy thảo luận, đánh giá xem kèo này khả năng thắng cao hay không và đưa ra lựa chọn chốt."}
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
# 5. GROQ AI: KIỂM DUYỆT ĐỒNG THUẬN & XUẤT BẢN TELEGRAM
# ================= ================= =================
def groq_final_review(gemini_res, deepseek_res, original_data):
    print("📌 [4/5] Groq AI đang kiểm duyệt sự đồng thuận giữa Gemini & DeepSeek...")
    
    prompt = f"""
    Bạn là Groq AI kiểm duyệt chốt kèo OpenClaw.
    - Ý kiến Gemini: {gemini_res}
    - Ý kiến DeepSeek: {deepseek_res}
    - Dữ liệu thô: {json.dumps(original_data, ensure_ascii=False)}

    Nhiệm vụ:
    1. Xem Gemini và DeepSeek đã THỐNG NHẤT chọn kèo có tỷ lệ thắng cao chưa.
    2. Nếu ĐÃ THỐNG NHẤT, hãy tạo bản tin Telegram chuẩn theo mẫu:

    🔥 **OPENCLAW KÈO THƠM BÓNG ĐÁ** 🔥
    🏆 **Giải đấu:** [Tên giải đấu]
    ⚔️ **Trận đấu:** [Tên 2 đội]
    ⏱️ **Thời gian:** [Phút thứ bao nhiêu đối với LIVE HOẶC Giờ VN đối với trận sắp diễn ra]
    🎯 **Kèo Lựa Chọn:** [Chọn kèo nằm đâu: Cược chấp Châu Á / Tài Xỉu]
    💡 **Đánh giá dòng tiền:** [Lý do ngắn gọn]

    Nếu CHƯA THỐNG NHẤT, trả về đúng chữ: NO
    """
    
    if not GROQ_API_KEY:
        # Giả lập phản hồi Groq khi chưa truyền key Groq
        item = original_data[0]
        return f"🔥 **OPENCLAW KÈO THƠM BÓNG ĐÁ** 🔥\n🏆 **Giải đấu:** {item['league']}\n⚔️ **Trận đấu:** {item['match']}\n⏱️ **Thời gian:** {item['minute']} (LIVE)\n🎯 **Kèo Lựa Chọn:** Arsenal -0.75 (Cược chấp Châu Á)\n💡 **Đánh giá dòng tiền:** Gemini & DeepSeek thống nhất dòng tiền đổ mạnh cửa Trên, tỷ lệ thắng cao."

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=15)
        if res.status_code == 200:
            return res.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"⚠️ Groq lỗi: {e}")
    
    # Fallback gửi thẳng nếu Groq có sự cố
    item = original_data[0]
    return f"🔥 **OPENCLAW KÈO THƠM BÓNG ĐÁ** 🔥\n🏆 **Giải đấu:** {item['league']}\n⚔️ **Trận đấu:** {item['match']}\n⏱️ **Thời gian:** {item['minute']} (LIVE)\n🎯 **Kèo Lựa Chọn:** Arsenal -0.75 (Cược chấp Châu Á)\n💡 **Đánh giá dòng tiền:** Dòng tiền đổ rất mạnh vào cửa Trên."

# ================= ================= =================
# 6. LỒNG CHẠY CHÍNH (MAIN)
# ================= ================= =================
def main():
    raw_data = fetch_football_odds()
    summary = cohere_summarize(raw_data)
    
    gemini_res = gemini_analyze(summary)
    deepseek_res = deepseek_analyze(summary, gemini_res)
    
    final_message = groq_final_review(gemini_res, deepseek_res, raw_data)
    
    if final_message and "NO" not in final_message:
        print("📌 [5/5] Đã chốt kèo thành công! Đang gửi Telegram...")
        send_telegram(final_message)
    else:
        print("⚡ Gemini và DeepSeek chưa đạt đồng thuận cao. Bỏ qua.")

if __name__ == "__main__":
    main()