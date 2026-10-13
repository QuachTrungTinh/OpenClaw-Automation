import os
from dotenv import load_dotenv

# Tải cấu hình từ file .env
load_dotenv()

env = os.getenv("SYSTEM_ENV", "unknown")
status = os.getenv("BOT_STATUS", "inactive")

print(f"--- OPENCLAW AUTOMATION SYSTEM ---")
print(f"Môi trường hiện tại: {env}")
print(f"Trạng thái Bot: {status}")
print(f"Hệ thống khởi động thành công và sẵn sàng vận hành 24/7!")
