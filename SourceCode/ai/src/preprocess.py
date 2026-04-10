import re
from underthesea import word_tokenize
import pandas as pd


# =========================
# CUSTOM MAPPING
# =========================
CUSTOM_MAPPING = {
   "sạc dự phòng": "sạc_dự_phòng",
   "bánh kem": "bánh_kem",
   "vở ghi chép": "vở_ghi_chép",
   "tai nghe": "tai_nghe",
   "trà đá": "trà_đá",
   "trà sữa": "trà_sữa",
   "sữa tắm": "sữa_tắm",
   "xem phim": "xem_phim",
   "rau củ": "rau_củ",
   "trà chanh": "trà_chanh",
   "rửa chén": "rửa_chén",
   "vá lốp": "vá_lốp"
}


# =========================
# PREPROCESS
# =========================
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


# =========================
# HELPER
# =========================
def contains(text, patterns):
   return any(re.search(p, text) for p in patterns)


# =========================
# CLASSIFIER
# =========================
def classify_category(text):
   text = text.lower()


   # =========================
   # 1.
   # =========================
   if contains(text, [
       r"lương", r"thưởng", r"nhận", r"lì xì", r"trúng",
       r"được cho", r"cho tiền", r"bán", r"thu nhập"
   ]) or contains(text, [
       r"hoàn tiền", r"refund", r"cashback"
   ]):
       return "Thu nhập"
   # =========================
   # 2.
   # =========================
   if contains(text, [
       r"mất tiền", r"mất \d+k",
       r"bị phạt", r"phạt xe",
       r"đền tiền", r"đền",
       r"đánh rơi",
       r"hỏng", r"vỡ",
       r"trễ hạn",
       r"xui", r"thủng"
   ]):
       return "Phát sinh"
   # =========================
   # 3. GIẢI TRÍ (fix phim + CGV)
   # =========================
   if contains(text, [
       r"xem_phim", r"cgv", r"netflix", r"spotify",
       r"game", r"karaoke"
   ]):
       return "Giải trí"


   # =========================
   # 4. ĂN UỐNG (fix bỏng nước)
   # =========================
   if contains(text, [
       r"ăn", r"uống", r"cơm", r"phở", r"bún",
       r"trà", r"cafe", r"xôi", r"bỏng", r"mì"
   ]):
       return "Ăn uống"


   # =========================
   # 5. SỨC KHỎE (đẩy xuống dưới ăn uống)
   # =========================
   if contains(text, [
       r"thuốc", r"vitamin", r"khám",
       r"bệnh", r"đau", r"ốm"]
   ):
       return "Sức khỏe"
   # =========================
   # 6. HÓA ĐƠN (fix lại)
   # =========================
   if contains(text, [
       r"điện",r"tiền_nước", r"wifi", r"mạng", r"thuê",
       r"bột giặt", r"nước rửa chén",r"sim", r"icloud",
       r"khăn giấy", r"xà phòng", r"tiền phòng"
   ]):
       return "Hóa đơn"


   # =========================
   # 7. DI CHUYỂN
   # =========================
   if contains(text, [
       r"xăng", r"xe", r"grab", r"bus", r"taxi"
   ]):
       return "Di chuyển"


   # =========================
   # 8. HỌC TẬP (fix recall)
   # =========================
   if contains(text, [
       r"sách", r"giáo_trình", r"tài_liệu",
       r"vở", r"usb", r"laptop", r"chuột"
   ]):
       return "Học tập"


   # =========================
   # 9. GIAO LƯU
   # =========================
   if contains(text, [
       r"tặng", r"sinh_nhật", r"cưới",
       r"bạn", r"người_yêu"
   ]):
       return "Giao lưu"


   return "Mua sắm"
# =========================
# RUN PIPELINE
# =========================
input_path = "../data/dataset_v1.csv"
output_path = "../data/dataset_v1_clean.csv"


try:
   print("Đang đọc file...")
   df = pd.read_csv(input_path, encoding='utf-8-sig')


   print("Preprocess...")
   df['clean_text'] = df['Raw Text (Câu văn thô)'].apply(preprocess_vni)


   print("Auto labeling...")
   df['auto_category'] = df['clean_text'].apply(classify_category)


   print("Lưu file...")
   df.to_csv(output_path, index=False, encoding='utf-8-sig')


   print(f"\n✅ DONE → {output_path}")


except Exception as e:
   print("❌ ERROR:", e)
