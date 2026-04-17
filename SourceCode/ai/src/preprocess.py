import re
from underthesea import word_tokenize
import pandas as pd

CUSTOM_MAPPING = {
    "sạc dự phòng": "sạc_dự_phòng", "bánh kem": "bánh_kem", "vở ghi chép": "vở_ghi_chép",
    "tai nghe": "tai_nghe", "trà đá": "trà_đá", "trà sữa": "trà_sữa", "sữa tắm": "sữa_tắm",
    "xem phim": "xem_phim", "rau củ": "rau_củ", "trà chanh": "trà_chanh",
    "rửa chén": "rửa_chén", "vá lốp": "vá_lốp"
}


def preprocess_vni(text):
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = word_tokenize(text, format="text")
    text = re.sub(r'(\d+)\s+(k|tr|củ|triệu|đ|nghìn|ngàn)', r'\1\2', text)
    text = " ".join(text.split())
    for wrong, correct in CUSTOM_MAPPING.items():
        text = text.replace(wrong, correct)
    return text


if __name__ == "__main__":
    input_path = "../data/dataset_v1.csv"
    output_path = "../data/dataset_v1_clean.csv"
    try:
        df = pd.read_csv(input_path, encoding='utf-8-sig')
        df['clean_text'] = df['Raw Text (Câu văn thô)'].apply(preprocess_vni)

        # CHỈ LƯU VĂN BẢN ĐÃ LÀM SẠCH, BỎ PHẦN GÁN NHÃN TỰ ĐỘNG
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f" HOÀN TẤT! Dữ liệu sạch đã lưu tại: {output_path}")
    except Exception as e:
        print(" LỖI:", e)