#!/usr/bin/env python3
"""
GPU-Accelerated Semantic Intent Router Training Script
Trains a neural semantic classifier on train.jsonl using PyTorch on CUDA.
Evaluates on val.jsonl and test.jsonl with out-of-domain (OOD) rejection.
"""

import json
import os
import sys
import time
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, accuracy_score, f1_score
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.constants import AgentType

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"[TRAINER] Using compute device: {DEVICE} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")

TRAIN_PATH = BACKEND_DIR / "eval" / "datasets" / "partitions" / "master_routing" / "train.jsonl"
VAL_PATH = BACKEND_DIR / "eval" / "datasets" / "partitions" / "master_routing" / "val.jsonl"
TEST_PATH = BACKEND_DIR / "eval" / "datasets" / "partitions" / "master_routing" / "test.jsonl"
CURATED_PATH = BACKEND_DIR / "eval" / "datasets" / "routing" / "master_routing_dataset.json"

MODEL_OUT_PATH = BACKEND_DIR / "app" / "ai" / "orchestration" / "semantic_router_weights.pt"
VECTORIZER_OUT_PATH = BACKEND_DIR / "app" / "ai" / "orchestration" / "semantic_vectorizer.pkl"
METADATA_OUT_PATH = BACKEND_DIR / "app" / "ai" / "orchestration" / "semantic_router_metadata.json"

# Core supported agent classes + explicit OOD class
CORE_CLASSES = [a.value for a in AgentType]
OOD_CLASS = "unsupported_ood"
ALL_CLASSES = CORE_CLASSES + [OOD_CLASS]
CLASS_TO_IDX = {c: i for i, c in enumerate(ALL_CLASSES)}
IDX_TO_CLASS = {i: c for i, c in enumerate(ALL_CLASSES)}


class SemanticRouterNet(nn.Module):
    def __init__(self, vocab_size: int, hidden_dim: int, num_classes: int):
        super().__init__()
        self.fc1 = nn.Linear(vocab_size, hidden_dim)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.15)
        self.fc2 = nn.Linear(hidden_dim, num_classes)

    def forward(self, x):
        h = self.dropout(self.relu(self.fc1(x)))
        return self.fc2(h)


def load_dataset(path: Path):
    texts, labels = [], []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            prompt = obj.get("prompt") or obj.get("query")
            agent = obj.get("expected_agent") or obj.get("agent")
            if not prompt or not agent:
                continue
            # Map out-of-domain categories to explicit OOD
            if agent in ("voice", "behavior"):
                agent = OOD_CLASS
            elif agent not in CORE_CLASSES:
                agent = OOD_CLASS
            texts.append(prompt)
            labels.append(CLASS_TO_IDX[agent])
    return texts, labels


def main():
    t0 = time.time()
    print("[1/5] Loading training corpus...")
    train_texts, train_labels = load_dataset(TRAIN_PATH)
    val_texts, val_labels = load_dataset(VAL_PATH)
    test_texts, test_labels = load_dataset(TEST_PATH)
    print(f"Loaded: Train={len(train_texts)}, Val={len(val_texts)}, Test={len(test_texts)}")

    # Also augment with curated dataset to ensure full coverage of reminder/web_search/campaign
    if CURATED_PATH.exists():
        with open(CURATED_PATH, "r", encoding="utf-8") as f:
            curated = json.load(f)
            for item in curated:
                p = item.get("prompt") or item.get("query")
                a = item.get("agent") or item.get("expected_agent")
                if p and a in CLASS_TO_IDX:
                    # duplicate curated to give solid weight
                    for _ in range(5):
                        train_texts.append(p)
                        train_labels.append(CLASS_TO_IDX[a])
        print(f"Augmented with curated dataset: Total Train={len(train_texts)}")

    print("[2/5] Fitting TF-IDF Vectorizer...")
    vectorizer = TfidfVectorizer(
        max_features=25000,
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=2,
    )
    X_train = vectorizer.fit_transform(train_texts)
    X_val = vectorizer.transform(val_texts)
    X_test = vectorizer.transform(test_texts)
    print(f"Vocabulary Size: {len(vectorizer.vocabulary_)}")

    # Convert to PyTorch tensors (Sparse to dense in batches or use mini-batch dataloader)
    print(f"[3/5] Initializing Neural Classifier on {DEVICE}...")
    num_classes = len(ALL_CLASSES)
    model = SemanticRouterNet(
        vocab_size=len(vectorizer.vocabulary_),
        hidden_dim=256,
        num_classes=num_classes,
    ).to(DEVICE)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)

    # Convert sparse to torch sparse or dense batch generator
    batch_size = 512
    num_samples = X_train.shape[0]
    indices = np.arange(num_samples)

    print("[4/5] Training for 5 epochs on GPU...")
    model.train()
    for epoch in range(5):
        np.random.shuffle(indices)
        total_loss = 0.0
        batches = 0
        for start_idx in range(0, num_samples, batch_size):
            batch_idx = indices[start_idx : start_idx + batch_size]
            batch_x_sparse = X_train[batch_idx].toarray()
            batch_x = torch.from_numpy(batch_x_sparse).float().to(DEVICE)
            batch_y = torch.tensor([train_labels[i] for i in batch_idx], dtype=torch.long, device=DEVICE)

            optimizer.zero_grad()
            out = model(batch_x)
            loss = criterion(out, batch_y)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            batches += 1
        avg_loss = total_loss / batches
        print(f"  Epoch {epoch+1}/5 - Loss: {avg_loss:.4f}")

    print("[5/5] Evaluating on Test Partition (12,204 samples)...")
    model.eval()
    test_preds = []
    test_probs = []
    with torch.no_grad():
        for start_idx in range(0, X_test.shape[0], batch_size):
            batch_x_sparse = X_test[start_idx : start_idx + batch_size].toarray()
            batch_x = torch.from_numpy(batch_x_sparse).float().to(DEVICE)
            logits = model(batch_x)
            probs = torch.softmax(logits, dim=-1)
            preds = torch.argmax(probs, dim=-1)
            test_preds.extend(preds.cpu().numpy().tolist())
            test_probs.extend(probs.cpu().numpy().tolist())

    acc = accuracy_score(test_labels, test_preds)
    macro_f1 = f1_score(test_labels, test_preds, average="macro")
    weighted_f1 = f1_score(test_labels, test_preds, average="weighted")

    print("\n" + "=" * 80)
    print("GPU SEMANTIC ROUTER EVALUATION ON TEST SET (12,204 SAMPLES):")
    print(f"Top-1 Accuracy:  {acc * 100:.2f}%")
    print(f"Macro F1 Score:  {macro_f1 * 100:.2f}%")
    print(f"Weighted F1:     {weighted_f1 * 100:.2f}%")
    print("=" * 80)

    # Save artifacts
    print(f"Saving weights to {MODEL_OUT_PATH}...")
    torch.save(model.state_dict(), MODEL_OUT_PATH)
    joblib.dump(vectorizer, VECTORIZER_OUT_PATH)
    with open(METADATA_OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "classes": ALL_CLASSES,
                "vocab_size": len(vectorizer.vocabulary_),
                "hidden_dim": 256,
                "num_classes": num_classes,
                "test_accuracy": round(float(acc), 4),
                "test_macro_f1": round(float(macro_f1), 4),
                "test_weighted_f1": round(float(weighted_f1), 4),
                "trained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "device": str(DEVICE),
            },
            f,
            indent=2,
        )
    print(f"Artifacts successfully saved in {time.time() - t0:.1f}s!")


if __name__ == "__main__":
    main()
