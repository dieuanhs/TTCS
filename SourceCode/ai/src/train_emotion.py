import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import classification_report
from utils import save_evaluation_log

MODEL_NAME = "vinai/phobert-base-v2"

# ============================
# 1. THIẾT LẬP DEVICE
# ============================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Đang sử dụng thiết bị: {device}")

# ============================
# 2. LOAD VÀ XỬ LÝ DỮ LIỆU
# ============================
df = pd.read_csv("../data/dataset_v1_clean.csv")
df = df.dropna(subset=["clean_text", "Emotion"])

# Encode label
label_map = {"Tiêu cực": 0, "Bình thường": 1, "Tích cực": 2}
df["label"] = df["Emotion"].map(label_map)

train_texts, test_texts, train_labels, test_labels = train_test_split(
    df["clean_text"], df["label"], test_size=0.15, random_state=42, stratify=df["label"]
)

# ============================
# 3. DATASET & DATALOADER
# ============================
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

class TextDataset(Dataset):
    def __init__(self, texts, labels):
        self.encodings = tokenizer(list(texts), truncation=True, padding=True, max_length=64)
        self.labels = list(labels)

    def __getitem__(self, idx):
        item = {k: torch.tensor(v[idx]) for k, v in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item

    def __len__(self):
        return len(self.labels)

train_dataset = TextDataset(train_texts, train_labels)
train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)

test_dataset = TextDataset(test_texts, test_labels)
test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False)

# ============================
# 4. KHỞI TẠO MÔ HÌNH
# ============================
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=3
)
model.to(device)

optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)

# ============================
# 5. VÒNG LẶP HUẤN LUYỆN (TRAIN)
# ============================
print("Bắt đầu huấn luyện...")
model.train()
for epoch in range(4):
    total_loss = 0
    for batch in train_loader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        outputs = model(input_ids, attention_mask=attention_mask, labels=labels)
        loss = outputs.loss
        total_loss += loss.item()

        loss.backward()
        optimizer.step()
        optimizer.zero_grad()

    avg_loss = total_loss / len(train_loader)
    print(f"Epoch {epoch+1}/4 hoàn tất - Loss: {avg_loss:.4f}")

# ============================
# 6. ĐÁNH GIÁ MÔ HÌNH (EVALUATE)
# ============================
print("Bắt đầu đánh giá...")
model.eval()
all_preds = []
all_labels = []

with torch.no_grad():
    for batch in test_loader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        outputs = model(input_ids, attention_mask=attention_mask)
        logits = outputs.logits

        preds = torch.argmax(logits, dim=1)

        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

print("=== Classification Report ===")
report = classification_report(all_labels, all_preds, target_names=["Tiêu cực", "Bình thường", "Tích cực"], zero_division=0)
print(report)

# lưu log
save_evaluation_log(
    model_name="PhoBERT-base-v2 (Emotion)",
    config_info="epochs=4, batch_size=16, lr=2e-5, max_length=64, input=clean_text",
    report_text=report
)

# ============================
# 7. LƯU MÔ HÌNH
# ============================
model.save_pretrained("../models/emotion_phobert")
tokenizer.save_pretrained("../models/emotion_phobert")
print(" Đã lưu mô hình thành công!")