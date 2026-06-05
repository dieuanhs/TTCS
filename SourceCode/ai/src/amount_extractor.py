import re


def extract_amount(text: str):
    text = text.lower().strip()

    text = re.sub(r'(\d+),(\d+)\s*(k|nghìn|ngàn|tr|triệu|củ|tỷ|tỉ)', r'\1.\2 \3', text)

    match_ruoi = re.search(r'([\d\.]+)\s*(k|nghìn|ngàn|tr|triệu|củ|tỷ|tỉ)\s*rưỡi', text)
    if match_ruoi:
        num = float(match_ruoi.group(1))
        unit = match_ruoi.group(2)
        if unit in ['k', 'nghìn', 'ngàn']:
            return int(num * 1000 + 500)
        elif unit in ['tr', 'triệu', 'củ']:
            return int(num * 1000000 + 500000)
        elif unit in ['tỷ', 'tỉ']:
            return int(num * 1000000000 + 500000000)

    match_noiduoi = re.search(r'([\d\.]+)\s*(k|nghìn|ngàn|tr|triệu|củ)\s*(\d{1,3})(?!\d)', text)
    if match_noiduoi:
        num1 = float(match_noiduoi.group(1))
        unit = match_noiduoi.group(2)
        num2_str = match_noiduoi.group(3)

        if unit in ['k', 'nghìn', 'ngàn']:
            # Ví dụ: 2k5 -> 2.5k -> 2500
            num2_val = int(num2_str) * (10 ** (3 - len(num2_str)))
            return int(num1 * 1000 + num2_val)
        elif unit in ['tr', 'triệu', 'củ']:
            # Ví dụ: 1tr6 -> 1.6tr -> 1600000
            num2_val = int(num2_str) * (10 ** (6 - len(num2_str)))
            return int(num1 * 1000000 + num2_val)

    match_donvi = re.search(r'([\d\.]+)\s*(k|nghìn|ngàn|tr|triệu|củ|tỷ|tỉ|lít|lốp)', text)
    if match_donvi:
        num = float(match_donvi.group(1))
        unit = match_donvi.group(2)

        if unit in ['k', 'nghìn', 'ngàn']:
            return int(num * 1000)
        elif unit in ['tr', 'triệu', 'củ']:
            return int(num * 1000000)
        elif unit in ['lít', 'lốp']:  # Tiếng lóng: 1 lít/lốp = 100.000đ
            return int(num * 100000)
        elif unit in ['tỷ', 'tỉ']:
            return int(num * 1000000000)

    match_pure = re.search(r'(?<![\d\.,])(\d{1,3}(?:[\.,]\d{3})+|\d{4,})(?![\d\.,])', text)
    if match_pure:
        num_str = match_pure.group(1).replace('.', '').replace(',', '')
        return int(num_str)

    match_fallback = re.search(r"\b\d+\b", text)
    if match_fallback:
        return int(match_fallback.group())

    return None