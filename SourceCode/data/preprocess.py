import re
from underthesea import word_tokenize
import pandas as pd

# TỪ ĐIỂN TÙY CHỈNH (Bạn cứ thêm từ thoải mái)
CUSTOM_MAPPING = {
    "sạc dự phòng": "sạc_dự_phòng",
    "sạc dự_phòng": "sạc_dự_phòng",
    "bánh kem": "bánh_kem",
    "vở ghi chép": "vở_ghi_chép",
    "vở ghi_chép": "vở_ghi_chép",
    "tai nghe": "tai_nghe",
    "mì tôm trữ": "mì_tôm trữ",
    "mì tôm_trữ": "mì_tôm trữ",
    "trà đá": "trà_đá",
    "trà sữa": "trà_sữa",
    "sữa tắm": "sữa_tắm",
    "cầu lông": "cầu_lông",
    "xem phim": "xem_phim",
    "bỏng nước": "bỏng_nước",
    "rau củ": "rau_củ",
    "trà chanh":"trà_chanh"
}


def preprocess_vni(text):
    if pd.isna(text):
        return ""

    # 1. Chuyển chữ thường và xóa ký tự đặc biệt
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', ' ', text)

    # 2. Tách từ bằng AI trước
    text = word_tokenize(text, format="text")

    # 3. Nối số tiền (120 k -> 120k)
    text = re.sub(r'(\d+)\s+(k|tr|củ|triệu|đ|nghìn|ngàn)', r'\1\2', text)

    # 4. Ép phẳng khoảng trắng
    text = " ".join(text.split())

    # 5. DÙNG TỪ ĐIỂN SỬA LỖI SAU CÙNG (Chắc chắn 100% ăn)
    for wrong_word, correct_word in CUSTOM_MAPPING.items():
        if wrong_word in text:
            text = text.replace(wrong_word, correct_word)

    return text


# =========================================================
# THỰC THI TRÊN FILE CSV
# =========================================================
input_path = "dataset_v1.csv"
output_path = "dataset_v1_clean.csv"

try:
    print("Đang đọc file dữ liệu...")
    df = pd.read_csv(input_path, encoding='utf-8-sig')

    print("Đang chuẩn hóa văn bản, vui lòng đợi...")
    df['clean_text'] = df['Raw Text (Câu văn thô)'].apply(preprocess_vni)

    # Cố gắng lưu file
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n--> THÀNH CÔNG! Đã lưu file mới tại '{output_path}'.")

except PermissionError:
    print("\n[LỖI NGHIÊM TRỌNG]: Không thể lưu file!")
    print("-> Ánh ơi, bạn đang MỞ file Excel đúng không? Hãy TẮT Excel đi rồi chạy lại code nhé!")
except FileNotFoundError:
    print(f"\n[LỖI]: Không tìm thấy file gốc tại {input_path}")