import re


def extract_amount(text):
    text = text.lower()
    total = 0
    pattern = r"(\d+(?:[.,]\d+)?)\s*(k|nghìn|ngàn|triệu|tr|củ)(?!\w)"

    matches = re.findall(pattern, text)

    for num_str, unit in matches:
        # kiểu float
        num_str = num_str.replace(',', '.')
        val = float(num_str)

        # Phân loại để nhân tiền
        if unit in ['k', 'nghìn', 'ngàn']:
            total += val * 1000
        elif unit in ['tr', 'triệu', 'củ']:
            total += val * 1000000

    # không có đơn vị
    if total == 0:
        match = re.search(r"\b\d+\b", text)
        if match:
            return int(match.group())

    return int(total) if total > 0 else None


