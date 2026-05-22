import torch
import torch.nn as nn
import pandas as pd
import numpy as np
import random
import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import classification_report, f1_score, accuracy_score
from torch.utils.data import Dataset, DataLoader
from utils import save_evaluation_log
from tqdm import tqdm

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # Thư mục src/
DATA_FILE = os.path.join(CURRENT_DIR, "../data/dataset_v1_clean.csv")
MODEL_SAVE_DIR = os.path.join(CURRENT_DIR, "../models/emotion_phobert")
MODEL_BACKUP_DIR = os.path.join(CURRENT_DIR, "../models/emotion_phobert_v2")
PTH_FILE = os.path.join(CURRENT_DIR, "../models/emotion_phobert.pth")

MODEL_NAME = "vinai/phobert-base-v2"
MAX_LENGTH = 64
BATCH_SIZE = 16
EPOCHS = 6
LR = 3e-5
PATIENCE = 2


# ============================
# 1. THIẾT LẬP (SEED & DEVICE)
# ============================
def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


set_seed(42)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Đang sử dụng thiết bị: {device}")

# ============================
# 2. LOAD VÀ XỬ LÝ DỮ LIỆU
# ============================
df = pd.read_csv(DATA_FILE)
df = df.dropna(subset=["clean_text", "Emotion"])
df["Emotion"] = df["Emotion"].astype(str).str.strip()

# Encode label
label_map = {"Tiêu cực": 0, "Bình thường": 1, "Tích cực": 2}
df["label"] = df["Emotion"].map(label_map)

train_texts, val_texts, train_labels, val_labels = train_test_split(
    df["clean_text"], df["label"], test_size=0.15, random_state=42, stratify=df["label"]
)

# Soft Class Weights
classes = np.unique(train_labels)
raw_weights = compute_class_weight(class_weight='balanced', classes=classes, y=train_labels)
soft_weights = np.log1p(raw_weights) + 0.5
class_weights = torch.tensor(soft_weights, dtype=torch.float).to(device)

# ============================
# 3. DATASET & DATALOADER
# ============================
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)


class TextDataset(Dataset):
    def __init__(self, texts, labels):
        self.encodings = tokenizer(list(texts), truncation=True, padding=True, max_length=MAX_LENGTH)
        self.labels = list(labels)

    def __getitem__(self, idx):
        item = {k: torch.tensor(v[idx]) for k, v in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item

    def __len__(self):
        return len(self.labels)


train_dataset = TextDataset(train_texts, train_labels)
train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)

val_dataset = TextDataset(val_texts, val_labels)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)

# ============================
# 4. KHỞI TẠO MÔ HÌNH & OPTIMIZER
# ============================
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=3)
model.to(device)

optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)

# Scheduler (Warmup)
total_steps = len(train_loader) * EPOCHS
scheduler = get_linear_schedule_with_warmup(
    optimizer,
    num_warmup_steps=int(total_steps * 0.1),
    num_training_steps=total_steps
)

# Loss
loss_fn = nn.CrossEntropyLoss(weight=class_weights)
scaler = torch.cuda.amp.GradScaler(enabled=(device.type == 'cuda'))

# ============================
# 5. VÒNG LẶP HUẤN LUYỆN (TRAIN & VAL)
# ============================
print("\nBắt đầu huấn luyện...")
best_val_macro_f1 = 0.0
best_model_state = None
epochs_no_improve = 0

for epoch in range(EPOCHS):
    model.train()
    total_train_loss = 0

    train_loop = tqdm(train_loader, desc=f"Epoch {epoch + 1}/{EPOCHS} [Train]")
    for batch in train_loop:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        optimizer.zero_grad()

        with torch.cuda.amp.autocast(enabled=(device.type == 'cuda')):
            outputs = model(input_ids, attention_mask=attention_mask)
            loss = loss_fn(outputs.logits, labels)

        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

        scaler.step(optimizer)
        scaler.update()
        scheduler.step()

        total_train_loss += loss.item()
        train_loop.set_postfix(loss=f"{loss.item():.4f}")

    avg_train_loss = total_train_loss / len(train_loader)

    model.eval()
    val_preds = []
    val_targets = []
    total_val_loss = 0

    with torch.no_grad():
        for batch in val_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            with torch.cuda.amp.autocast(enabled=(device.type == 'cuda')):
                outputs = model(input_ids, attention_mask=attention_mask)
                loss = loss_fn(outputs.logits, labels)

            total_val_loss += loss.item()
            preds = torch.argmax(outputs.logits, dim=1)

            val_preds.extend(preds.cpu().numpy())
            val_targets.extend(labels.cpu().numpy())

    avg_val_loss = total_val_loss / len(val_loader)
    val_macro_f1 = f1_score(val_targets, val_preds, average="macro")
    val_acc = accuracy_score(val_targets, val_preds)

    print(
        f"Epoch {epoch + 1} - Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f} | Val Acc: {val_acc:.4f} | Val Macro F1: {val_macro_f1:.4f}")

    if val_macro_f1 > best_val_macro_f1:
        best_val_macro_f1 = val_macro_f1
        best_model_state = model.state_dict().copy()
        epochs_no_improve = 0
        print(f"-> Macro F1 tăng lên {best_val_macro_f1:.4f}, đã lưu Checkpoint.")
    else:
        epochs_no_improve += 1
        print(f"-> Macro F1 không tăng. Patience: {epochs_no_improve}/{PATIENCE}")
        if epochs_no_improve >= PATIENCE:
            print(" KÍCH HOẠT EARLY STOPPING!")
            break

if best_model_state:
    model.load_state_dict(best_model_state)

# ============================
# 6. ĐÁNH GIÁ MÔ HÌNH
# ============================
print("\n=== Final Classification Report ===")
report = classification_report(val_targets, val_preds, target_names=["Tiêu cực", "Bình thường", "Tích cực"],
                               zero_division=0)
print(report)

save_evaluation_log(
    model_name="PhoBERT-base-v2 (Production Pipeline v2)",
    config_info=f"epochs={EPOCHS} (Early Stop), batch={BATCH_SIZE}, lr={LR}, max_len={MAX_LENGTH}, Soft_Weights_Log",
    report_text=report
)

# ============================
# 7. LƯU MÔ HÌNH
# ============================
try:
    # 1. Lưu folder
    model.save_pretrained(MODEL_SAVE_DIR, safe_serialization=False)
    tokenizer.save_pretrained(MODEL_SAVE_DIR)

    # 2. Lưu file weights .pth
    torch.save(model.state_dict(), PTH_FILE)

    print(f"\n✅ Đã lưu thư mục HuggingFace vào: {MODEL_SAVE_DIR}")
    print(f"✅ Đã lưu file weights vào: {PTH_FILE}")
except Exception as e:
    print(f"\n⚠️ Cảnh báo: File bị khóa do Backend đang chạy ({e}).")
    print(f"🔄 Đang tự động chuyển hướng lưu sang thư mục backup...")

    model.save_pretrained(MODEL_BACKUP_DIR, safe_serialization=False)
    tokenizer.save_pretrained(MODEL_BACKUP_DIR)

    backup_pth = os.path.join(CURRENT_DIR, "../models/emotion_phobert_v2.pth")
    torch.save(model.state_dict(), backup_pth)

    print(f"✅ Đã lưu an toàn vào thư mục backup: {MODEL_BACKUP_DIR}")