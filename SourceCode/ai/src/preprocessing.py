import re

def clean_text(text):
    text = text.lower()
    text = re.sub(r"\d+k", lambda x: str(int(x.group()[:-1]) * 1000), text)
    text = re.sub(r"[^a-zA-Z0-9àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text