import re

def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)  # bỏ ký tự đặc biệt
    return text