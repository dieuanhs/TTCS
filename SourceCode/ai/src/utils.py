import os
from datetime import datetime

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")


def save_evaluation_log(model_name: str, config_info: str, report_text: str):
    """
    Lưu kết quả Classification Report vào file logs/evaluation.txt
    """
    # 1. Tự động tạo thư mục logs nếu nó chưa tồn tại
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    log_file = os.path.join(LOG_DIR, "evaluation.txt")

    # 2. Lấy thời gian hiện tại
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 3. ghi nối tiếp
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f" THỜI GIAN: {now}\n")
        f.write(f" MÔ HÌNH:   {model_name}\n")
        f.write(f"CẤU HÌNH:  {config_info}\n")
        f.write(" KẾT QUẢ:\n")
        f.write(report_text + "\n")
        f.write("=" * 60 + "\n\n")

    print(f"Đã lưu lịch sử huấn luyện vào: {log_file}")