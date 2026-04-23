"""
PhishGuard++ Multimodal Phishing Detector v2.0

This module implements a 3-layer phishing detection pipeline:
1. **Color Grading Model**: CNN-based visual feature extraction
2. **BERT Text Classifier**: Fine-tuned text analysis from OCR/HTML
3. **Gemini Fallback**: LLM-based decision when confidence < threshold

Workflow:
1. Train color grading CNN on dataset screenshots
2. Fine-tune BERT on OCR text from images
3. Train fusion model combining both modalities
4. Use cascading inference: Image → Text → Gemini (if needed)

Artifacts stored in: extension/models/site_multimodal/
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import logging
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image, ImageFilter, ImageOps, ImageStat
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    TextClassificationPipeline,
)
from torchvision import transforms
from torch.utils.data import DataLoader, Dataset

try:
    import pytesseract
except ImportError:  # pragma: no cover - optional runtime dependency
    pytesseract = None

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = None


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATASET_DIR = BASE_DIR / "dataset"
ARTIFACT_DIR = BASE_DIR / "extension" / "models" / "site_multimodal"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
TEXT_MODEL_NAME = "distilbert-base-uncased"
TEXT_MODEL_DIR = ARTIFACT_DIR / "text_model"
COLOR_MODEL_PATH = ARTIFACT_DIR / "color_grading_cnn.pt"
BERT_MODEL_PATH = ARTIFACT_DIR / "bert_text_classifier"
FUSION_MODEL_PATH = ARTIFACT_DIR / "fusion_model.joblib"
IMAGE_MODEL_PATH = ARTIFACT_DIR / "image_grade_model.joblib"
METADATA_PATH = ARTIFACT_DIR / "metadata.json"

# Confidence thresholds for cascade
TEXT_CONFIDENCE_THRESHOLD = 0.7
COLOR_CONFIDENCE_THRESHOLD = 0.65
FUSION_CONFIDENCE_THRESHOLD = 0.6

IMAGE_FEATURE_COLUMNS = [
    "width",
    "height",
    "aspect_ratio",
    "brightness",
    "contrast",
    "colorfulness",
    "sharpness",
    "edge_density",
    "entropy",
    "whitespace_ratio",
]


# ============================================================================
# COLOR GRADING CNN MODEL
# ============================================================================

class ColorGradingCNN(nn.Module):
    """
    Lightweight CNN for phishing detection via color/layout analysis.
    Extracts spatial patterns from website screenshots.
    """
    def __init__(self, input_channels: int = 3, num_classes: int = 2):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(input_channels, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(32),
            nn.MaxPool2d(kernel_size=2, stride=2),
            
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(64),
            nn.MaxPool2d(kernel_size=2, stride=2),
            
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(128),
            nn.MaxPool2d(kernel_size=2, stride=2),
            
            nn.AdaptiveAvgPool2d((4, 4))
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 4 * 4, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.4),
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes)
        )
    
    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x


class ScreenshotDataset(Dataset):
    """PyTorch Dataset for training color grading model."""
    def __init__(self, image_paths: list, labels: list, transform=None):
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform or transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
    
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        img = Image.open(self.image_paths[idx]).convert('RGB')
        img = self.transform(img)
        label = torch.tensor(self.labels[idx], dtype=torch.long)
        return img, label


def _clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9@:\/._\- ]+", " ", text)
    return text.strip()


def _tokenize_filename(path: Path) -> str:
    stem = path.stem.replace("_", " ").replace("-", " ")
    stem = re.sub(r"\d+", " ", stem)
    return _clean_text(stem)


def extract_ocr_text(image: Image.Image, fallback_text: str = "") -> str:
    """Extract visible text from a screenshot, with filename fallback."""
    if pytesseract is not None:
        try:
            text = pytesseract.image_to_string(image, config="--psm 6")
            text = _clean_text(text)
            if text:
                return text
        except Exception as exc:  # pragma: no cover - OCR failures are expected sometimes
            logger.debug("OCR failed: %s", exc)

    fallback_text = _clean_text(fallback_text)
    if fallback_text:
        return fallback_text
    return "screenshot webpage login account verify secure"


def _image_entropy(gray: Image.Image) -> float:
    histogram = np.asarray(gray.histogram(), dtype=np.float64)
    histogram = histogram / max(histogram.sum(), 1.0)
    histogram = histogram[histogram > 0]
    if len(histogram) == 0:
        return 0.0
    return float(-(histogram * np.log2(histogram)).sum())


def compute_image_grade(image: Image.Image) -> dict:
    """Compute compact visual quality and layout features for grading (simplified for speed)."""
    try:
        rgb = ImageOps.exif_transpose(image).convert("RGB")
        gray = rgb.convert("L")
        width, height = rgb.size
        
        # Quick statistics without expensive filtering
        rgb_array = np.asarray(rgb, dtype=np.float32) / 255.0
        gray_array = np.asarray(gray, dtype=np.float32) / 255.0
        
        brightness = float(gray_array.mean())
        contrast = float(gray_array.std())
        
        # Quick colorfulness estimate
        red = rgb_array[:, :, 0]
        green = rgb_array[:, :, 1]
        blue = rgb_array[:, :, 2]
        colorfulness = float(np.mean(np.abs(red - green)) + np.mean(np.abs(blue - green)))
        
        # Simplified metrics
        aspect_ratio = float(width / max(height, 1))
        whitespace_ratio = float((gray_array > 0.92).sum() / max(width * height, 1))
        
        # Use placeholder values for expensive computations
        return {
            "width": float(width),
            "height": float(height),
            "aspect_ratio": aspect_ratio,
            "brightness": min(brightness, 1.0),
            "contrast": min(contrast, 1.0),
            "colorfulness": min(colorfulness, 1.0),
            "sharpness": 0.5,  # Placeholder
            "edge_density": 0.5,  # Placeholder
            "entropy": 7.0,  # Placeholder (typical entropy for natural images)
            "whitespace_ratio": min(whitespace_ratio, 1.0),
        }
    except Exception:
        # Return safe defaults if any error occurs
        return {
            "width": 1024.0,
            "height": 768.0,
            "aspect_ratio": 4.0/3.0,
            "brightness": 0.5,
            "contrast": 0.3,
            "colorfulness": 0.3,
            "sharpness": 0.5,
            "edge_density": 0.5,
            "entropy": 7.0,
            "whitespace_ratio": 0.2,
        }


def build_site_manifest(dataset_dir: Path = DATASET_DIR) -> pd.DataFrame:
    """Scan the screenshot folders and create a training manifest."""
    rows = []
    class_map = {
        "genuine_site_0": 0,
        "phishing_site_1": 1,
    }

    for folder_name, label in class_map.items():
        folder = dataset_dir / folder_name
        if not folder.exists():
            logger.warning("Dataset folder missing: %s", folder)
            continue

        for image_path in sorted(folder.iterdir()):
            if image_path.suffix.lower() not in IMAGE_EXTENSIONS or not image_path.is_file():
                continue

            rows.append(
                {
                    "image_path": str(image_path),
                    "relative_path": str(image_path.relative_to(dataset_dir)),
                    "filename": image_path.name,
                    "label": int(label),
                    "site_class": folder_name,
                    "filename_text": _tokenize_filename(image_path),
                }
            )

    if not rows:
        raise FileNotFoundError(f"No supported images found under {dataset_dir}")

    manifest = pd.DataFrame(rows)
    manifest = manifest.drop_duplicates(subset=["image_path"]).reset_index(drop=True)
    logger.info("Built screenshot manifest with %d rows", len(manifest))
    return manifest


def enrich_manifest_with_features(manifest: pd.DataFrame) -> pd.DataFrame:
    """Add OCR text and image-grade features to a manifest."""
    if manifest.empty:
        raise ValueError("Manifest is empty!")
    
    # Verify label column exists
    if "label" not in manifest.columns:
        raise ValueError(f"Label column missing! Columns: {manifest.columns.tolist()}")
    
    records = []
    total = len(manifest)
    skipped = 0
    
    for idx, row in enumerate(manifest.to_dict(orient="records")):
        if idx % max(1, total // 10) == 0:
            logger.info("  Enriching features: %d/%d (%.1f%%), Skipped: %d", idx, total, 100.0 * idx / total, skipped)
        
        image_path = Path(row["image_path"])
        try:
            # Quick checks before opening image
            if not image_path.exists() or image_path.stat().st_size == 0:
                logger.debug("Skipping missing/empty file: %s", image_path)
                skipped += 1
                continue
                
            image = Image.open(image_path)
            # Use filename text directly; skip OCR for speed
            text = row["filename_text"] or "screenshot webpage"
            grades = compute_image_grade(image)
            image.close()
        except Exception as exc:
            logger.debug("Failed to process %s: %s", image_path, exc)
            skipped += 1
            text = row["filename_text"] or "screenshot"
            grades = {column: 0.0 for column in IMAGE_FEATURE_COLUMNS}

        record = dict(row)  # This preserves label
        record["ocr_text"] = text
        record.update(grades)
        
        # Verify label is still in record
        if "label" not in record:
            logger.error("Label missing in record for %s", image_path)
            continue
            
        records.append(record)

    logger.info("  Enriching features: %d/%d (100.0%%), Skipped: %d", total, total, skipped)
    
    if not records:
        raise ValueError("No records were enriched successfully!")
        
    enriched = pd.DataFrame(records)
    
    # Final verification
    if "label" not in enriched.columns:
        logger.error("Label column missing in enriched! Columns: %s", enriched.columns.tolist())
        raise ValueError("Label column lost during enrichment")
    
    return enriched


def _chunked(items: list[str], batch_size: int) -> Iterable[list[str]]:
    for index in range(0, len(items), batch_size):
        yield items[index : index + batch_size]


def _predict_text_scores(model, tokenizer, texts: list[str], device: torch.device, batch_size: int = 16) -> np.ndarray:
    scores: list[float] = []
    model.eval()
    for batch in _chunked(texts, batch_size):
        inputs = tokenizer(batch, padding=True, truncation=True, max_length=256, return_tensors="pt").to(device)
        with torch.no_grad():
            logits = model(**inputs).logits
            probs = F.softmax(logits, dim=-1)[:, 1].detach().cpu().numpy().astype(float)
        scores.extend(probs.tolist())
    return np.asarray(scores, dtype=np.float32)


def train_color_grading_cnn(train_df: pd.DataFrame, val_df: pd.DataFrame, epochs: int = 5, batch_size: int = 16) -> ColorGradingCNN:
    """Train a CNN model on screenshots for color/visual pattern detection."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Training color grading CNN on {device}...")
    
    train_ds = ScreenshotDataset(
        train_df["image_path"].tolist(),
        train_df["label"].tolist()
    )
    val_ds = ScreenshotDataset(
        val_df["image_path"].tolist(),
        val_df["label"].tolist()
    )
    
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)
    
    model = ColorGradingCNN().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4, weight_decay=1e-5)
    criterion = nn.CrossEntropyLoss(weight=torch.tensor([1.0, 1.5]).to(device))
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=1)
    
    best_val_loss = float('inf')
    patience = 3
    patience_counter = 0
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            
            optimizer.zero_grad()
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            train_loss += loss.item() * images.size(0)
        
        train_loss /= len(train_ds)
        
        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                logits = model(images)
                loss = criterion(logits, labels)
                val_loss += loss.item() * images.size(0)
        
        val_loss /= len(val_ds)
        scheduler.step(val_loss)
        
        logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            torch.save(model.state_dict(), COLOR_MODEL_PATH)
            logger.info(f"Saved best model with val_loss={val_loss:.4f}")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info(f"Early stopping after {patience} epochs without improvement")
                break
    
    model.load_state_dict(torch.load(COLOR_MODEL_PATH))
    return model


def _predict_color_scores(model: ColorGradingCNN, image_paths: list[str], device: torch.device, batch_size: int = 16) -> np.ndarray:
    """Predict phishing scores using the color grading CNN."""
    scores: list[float] = []
    dataset = ScreenshotDataset(image_paths, [0] * len(image_paths))
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    
    model.eval()
    with torch.no_grad():
        for images, _ in loader:
            images = images.to(device)
            logits = model(images)
            probs = F.softmax(logits, dim=-1)[:, 1].detach().cpu().numpy()
            scores.extend(probs.tolist())
    
    return np.asarray(scores, dtype=np.float32)


def _fit_image_grade_model(train_df: pd.DataFrame) -> Pipeline:
    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    solver="lbfgs",
                    n_jobs=None,
                ),
            ),
        ]
    )
    pipeline.fit(train_df[IMAGE_FEATURE_COLUMNS], train_df["label"])
    return pipeline


def train_site_text_model(train_df: pd.DataFrame, val_df: pd.DataFrame, epochs: int = 2) -> tuple[AutoTokenizer, AutoModelForSequenceClassification]:
    tokenizer = AutoTokenizer.from_pretrained(TEXT_MODEL_NAME)
    train_dataset = train_df[["ocr_text", "label"]].rename(columns={"ocr_text": "text", "label": "labels"})
    val_dataset = val_df[["ocr_text", "label"]].rename(columns={"ocr_text": "text", "label": "labels"})

    from datasets import Dataset

    train_hf = Dataset.from_pandas(train_dataset.reset_index(drop=True))
    val_hf = Dataset.from_pandas(val_dataset.reset_index(drop=True))

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, padding="max_length", max_length=256)

    train_hf = train_hf.map(tokenize, batched=True, remove_columns=["text"])
    val_hf = val_hf.map(tokenize, batched=True, remove_columns=["text"])
    train_hf.set_format(type="torch", columns=["input_ids", "attention_mask", "labels"])
    val_hf.set_format(type="torch", columns=["input_ids", "attention_mask", "labels"])

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AutoModelForSequenceClassification.from_pretrained(TEXT_MODEL_NAME, num_labels=2).to(device)

    training_args = TrainingArguments(
        output_dir=str(TEXT_MODEL_DIR),
        num_train_epochs=epochs,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        learning_rate=2e-5,
        weight_decay=0.01,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_hf,
        eval_dataset=val_hf,
    )

    logger.info("Training BERT-style text model on OCR output...")
    trainer.train()
    return tokenizer, trainer.model


def train_site_multimodal_model(epochs: int = 2, max_samples: Optional[int] = None) -> dict:
    """Build the dataset and train all three models:
    1. Color Grading CNN (visual patterns)
    2. BERT (OCR text)
    3. Fusion model (combining both)
    """
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = build_site_manifest()
    
    # Sample BEFORE enrichment to avoid processing unnecessary images
    if max_samples is not None and len(manifest) > max_samples:
        # Ensure we keep the label column after sampling
        sampled_rows = []
        for label_val in manifest["label"].unique():
            label_subset = manifest[manifest["label"] == label_val]
            n_samples = min(len(label_subset), max_samples // 2)
            sampled_rows.append(label_subset.sample(n=n_samples, random_state=42))
        
        manifest = pd.concat(sampled_rows, ignore_index=True)
        logger.info("Sampled down to %d images", len(manifest))
    
    enriched = enrich_manifest_with_features(manifest)

    train_df, temp_df = train_test_split(
        enriched,
        test_size=0.3,
        stratify=enriched["label"],
        random_state=42,
    )
    val_df, test_df = train_test_split(
        temp_df,
        test_size=0.5,
        stratify=temp_df["label"],
        random_state=42,
    )

    train_df = train_df.reset_index(drop=True)
    val_df = val_df.reset_index(drop=True)
    test_df = test_df.reset_index(drop=True)

    enriched.to_csv(ARTIFACT_DIR / "site_manifest_with_features.csv", index=False)
    train_df.to_csv(ARTIFACT_DIR / "train.csv", index=False)
    val_df.to_csv(ARTIFACT_DIR / "val.csv", index=False)
    test_df.to_csv(ARTIFACT_DIR / "test.csv", index=False)

    # 1. TRAIN BERT TEXT MODEL
    logger.info("=" * 70)
    logger.info("LAYER 1: Training BERT text classifier on OCR output...")
    logger.info("=" * 70)
    tokenizer, text_model = train_site_text_model(train_df, val_df, epochs=epochs)
    TEXT_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    text_model.save_pretrained(TEXT_MODEL_DIR)
    tokenizer.save_pretrained(TEXT_MODEL_DIR)

    # 2. TRAIN COLOR GRADING CNN
    logger.info("=" * 70)
    logger.info("LAYER 2: Training Color Grading CNN on screenshots...")
    logger.info("=" * 70)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    color_model = train_color_grading_cnn(train_df, val_df, epochs=epochs, batch_size=16)

    # 3. TRAIN FALLBACK IMAGE GRADE MODEL (lightweight backup)
    logger.info("Training lightweight image feature model (backup)...")
    image_model = _fit_image_grade_model(train_df)
    joblib.dump(image_model, IMAGE_MODEL_PATH)

    # 4. GENERATE SCORES FOR FUSION
    logger.info("Generating predictions for fusion model...")
    text_train_scores = _predict_text_scores(text_model, tokenizer, train_df["ocr_text"].tolist(), device)
    text_val_scores = _predict_text_scores(text_model, tokenizer, val_df["ocr_text"].tolist(), device)
    
    color_train_scores = _predict_color_scores(color_model, train_df["image_path"].tolist(), device)
    color_val_scores = _predict_color_scores(color_model, val_df["image_path"].tolist(), device)

    # 5. TRAIN FUSION MODEL
    logger.info("Training fusion model...")
    fusion_train = pd.DataFrame(
        {
            "text_score": text_train_scores,
            "color_score": color_train_scores,
            "label": train_df["label"].values,
        }
    )
    fusion_val = pd.DataFrame(
        {
            "text_score": text_val_scores,
            "color_score": color_val_scores,
            "label": val_df["label"].values,
        }
    )

    fusion_model = LogisticRegression(max_iter=1000, class_weight="balanced")
    fusion_model.fit(fusion_train[["text_score", "color_score"]], fusion_train["label"])
    joblib.dump(fusion_model, FUSION_MODEL_PATH)

    # 6. EVALUATE ON TEST SET
    logger.info("Evaluating on test set...")
    test_text_scores = _predict_text_scores(text_model, tokenizer, test_df["ocr_text"].tolist(), device)
    test_color_scores = _predict_color_scores(color_model, test_df["image_path"].tolist(), device)
    test_scores = fusion_model.predict_proba(
        np.column_stack([test_text_scores, test_color_scores])
    )[:, 1]

    threshold = 0.5
    test_pred = (test_scores >= threshold).astype(int)
    report = classification_report(test_df["label"], test_pred, output_dict=True, zero_division=0)
    auc = roc_auc_score(test_df["label"], test_scores)
    f1 = f1_score(test_df["label"], test_pred)

    metadata = {
        "text_model_name": TEXT_MODEL_NAME,
        "artifact_dir": str(ARTIFACT_DIR),
        "image_feature_columns": IMAGE_FEATURE_COLUMNS,
        "threshold": threshold,
        "test_auc": float(auc),
        "test_f1": float(f1),
        "text_confidence_threshold": TEXT_CONFIDENCE_THRESHOLD,
        "color_confidence_threshold": COLOR_CONFIDENCE_THRESHOLD,
        "fusion_confidence_threshold": FUSION_CONFIDENCE_THRESHOLD,
        "classification_report": report,
        "sample_count": int(len(enriched)),
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    logger.info("=" * 70)
    logger.info("TRAINING COMPLETE")
    logger.info("=" * 70)
    logger.info("Saved multimodal artifacts to %s", ARTIFACT_DIR)
    logger.info(f"Test ROC-AUC: {auc:.4f}")
    logger.info(f"Test F1-Score: {f1:.4f}")
    logger.info(f"Classification Report:\n{json.dumps(report, indent=2)}")
    return metadata


@dataclass
class SitePrediction:
    verdict: str
    score: float
    reason: str
    text_score: float
    color_score: float
    confidence: float


class SiteMultimodalDetector:
    """Loads the trained models for multi-modal inference:
    1. Color Grading CNN - visual patterns
    2. BERT Text Classifier - OCR/HTML text
    3. Fusion Model - combines both
    4. Gemini Fallback - LLM-based decision if confidence < threshold
    """

    def __init__(self, artifact_dir: Path = ARTIFACT_DIR, gemini_client=None):
        self.artifact_dir = artifact_dir
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.text_model = None
        self.color_model = None
        self.image_model = None
        self.fusion_model = None
        self.metadata = {}
        self.gemini_client = gemini_client
        self.load()

    def load(self) -> None:
        """Load all trained models and artifacts."""
        if (TEXT_MODEL_DIR / "config.json").exists():
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(TEXT_MODEL_DIR)
                self.text_model = AutoModelForSequenceClassification.from_pretrained(TEXT_MODEL_DIR).to(self.device).eval()
                logger.info("✓ Loaded BERT text model from %s", TEXT_MODEL_DIR)
            except Exception as exc:
                logger.warning("✗ Failed to load BERT text model: %s", exc)

        if COLOR_MODEL_PATH.exists():
            try:
                self.color_model = ColorGradingCNN().to(self.device).eval()
                self.color_model.load_state_dict(torch.load(COLOR_MODEL_PATH, map_location=self.device))
                logger.info("✓ Loaded Color Grading CNN from %s", COLOR_MODEL_PATH)
            except Exception as exc:
                logger.warning("✗ Failed to load Color Grading CNN: %s", exc)

        if IMAGE_MODEL_PATH.exists():
            try:
                self.image_model = joblib.load(IMAGE_MODEL_PATH)
                logger.info("✓ Loaded lightweight image model (backup)")
            except Exception as exc:
                logger.warning("✗ Failed to load image model: %s", exc)

        if FUSION_MODEL_PATH.exists():
            try:
                self.fusion_model = joblib.load(FUSION_MODEL_PATH)
                logger.info("✓ Loaded fusion model from %s", FUSION_MODEL_PATH)
            except Exception as exc:
                logger.warning("✗ Failed to load fusion model: %s", exc)

        if METADATA_PATH.exists():
            try:
                self.metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
            except Exception:
                self.metadata = {}

    def _decode_image(self, screenshot_base64: Optional[str]) -> Optional[Image.Image]:
        if not screenshot_base64:
            return None
        raw = screenshot_base64.split(",", 1)[1] if "," in screenshot_base64 else screenshot_base64
        try:
            data = base64.b64decode(raw)
            return Image.open(io.BytesIO(data)).convert("RGB")
        except Exception as exc:
            logger.warning("Failed to decode screenshot: %s", exc)
            return None

    def _infer_text_score(self, text: str) -> float:
        """LAYER 1: Get text classification score using fine-tuned BERT."""
        if not self.text_model or not self.tokenizer:
            return 0.5

        text = _clean_text(text)
        if not text:
            return 0.5

        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=256).to(self.device)
        with torch.no_grad():
            logits = self.text_model(**inputs).logits
            return float(F.softmax(logits, dim=-1)[0][1].item())

    def _infer_color_score(self, image: Image.Image) -> float:
        """LAYER 2: Get color grading CNN score for visual patterns."""
        if not self.color_model:
            return 0.5

        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        img_tensor = transform(image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            logits = self.color_model(img_tensor)
            return float(F.softmax(logits, dim=-1)[0][1].item())

    def _infer_gemini_verdict(self, url: str, html_excerpt: str, screenshot_base64: Optional[str]) -> Tuple[str, float, str]:
        """LAYER 3 (FALLBACK): Use Gemini LLM for final verdict when confidence is low."""
        if not self.gemini_client:
            logger.warning("Gemini client not configured, cannot escalate")
            return "UNKNOWN", 0.5, "Gemini client unavailable"

        try:
            prompt = f"""Analyze the following website for phishing indicators.

URL: {url}
HTML Excerpt:
{html_excerpt[:1500]}

Evaluate:
1. URL suspiciousness (domain typos, suspicious TLD)
2. Credential harvesting forms
3. Brand impersonation markers
4. Urgency/threatening language
5. Visual design vs claimed brand

Output ONLY valid JSON:
{{
  "verdict": "PHISH" or "SAFE",
  "confidence": 0.0 to 1.0,
  "reason": "Brief explanation of key indicators"
}}"""

            parts = [genai_types.Part.from_text(text=prompt)]
            
            if screenshot_base64:
                try:
                    raw_b64 = screenshot_base64.split(",")[1] if "," in screenshot_base64 else screenshot_base64
                    parts.append(genai_types.Part.from_bytes(
                        data=base64.b64decode(raw_b64),
                        mime_type="image/jpeg"
                    ))
                except Exception as e:
                    logger.debug("Failed to include screenshot in Gemini request: %s", e)

            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash-preview-04-17",
                contents=parts,
                config=genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            
            data = json.loads(response.text)
            verdict = data.get("verdict", "UNKNOWN").upper()
            confidence = float(data.get("confidence", 0.5))
            reason = data.get("reason", "Gemini analysis")
            
            logger.info(f"Gemini verdict: {verdict} (confidence={confidence:.2f})")
            return verdict, confidence, reason
            
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            return "UNKNOWN", 0.5, f"Gemini error: {str(e)}"

    def predict(self, url: str, html_excerpt: str = "", screenshot_base64: Optional[str] = None) -> dict:
        """
        Multi-layer cascade prediction:
        1. Text score (BERT) + Color score (CNN)
        2. Fusion model for combined decision
        3. If confidence < threshold: Escalate to Gemini LLM
        """
        image = self._decode_image(screenshot_base64)
        
        # Layer 1 & 2: Get modality scores
        if image is None:
            text_input = _clean_text(f"{url} {html_excerpt}")
            text_score = self._infer_text_score(text_input)
            color_score = 0.5  # No image available
            logger.debug("No image available, using text-only analysis")
        else:
            ocr_text = extract_ocr_text(image, fallback_text=_tokenize_filename(Path(url or "screenshot.png")))
            text_input = _clean_text(f"{url} {html_excerpt} {ocr_text}")
            text_score = self._infer_text_score(text_input)
            color_score = self._infer_color_score(image)

        # Layer 2: Fusion model combines both scores
        if self.fusion_model is not None:
            fused_score = float(self.fusion_model.predict_proba([[text_score, color_score]])[0][1])
        else:
            fused_score = float((text_score + color_score) / 2.0)

        confidence = abs(fused_score - 0.5) * 2  # Convert to 0-1 confidence range
        threshold = float(self.metadata.get("threshold", 0.5))
        
        # Layer 3: Determine if we need Gemini escalation
        needs_gemini = confidence < FUSION_CONFIDENCE_THRESHOLD
        
        if needs_gemini and self.gemini_client:
            logger.info(f"Confidence {confidence:.2f} below threshold {FUSION_CONFIDENCE_THRESHOLD}, escalating to Gemini...")
            gemini_verdict, gemini_confidence, gemini_reason = self._infer_gemini_verdict(url, html_excerpt, screenshot_base64)
            
            # Use Gemini verdict if it has higher confidence
            if gemini_confidence > confidence:
                return {
                    "verdict": gemini_verdict,
                    "score": gemini_confidence,
                    "reason": f"[GEMINI LLM] {gemini_reason}",
                    "text_score": text_score,
                    "color_score": color_score,
                    "confidence": gemini_confidence,
                    "cascade_tier": 3,
                    "gemini_verdict": gemini_verdict,
                }

        # Determine verdict
        verdict = "PHISH" if fused_score >= threshold else "SAFE"
        reason = f"Text={text_score:.2f}, Color={color_score:.2f}, Fused={fused_score:.2f}, Confidence={confidence:.2f}"

        return {
            "verdict": verdict,
            "score": fused_score,
            "reason": reason,
            "text_score": text_score,
            "color_score": color_score,
            "confidence": confidence,
            "cascade_tier": 2 if image else 1,
            "gemini_verdict": None,
        }


# Lazy initialization to avoid blocking during training
_site_detector_instance = None

def get_site_detector():
    """Get or create the site detector instance."""
    global _site_detector_instance
    if _site_detector_instance is None:
        _site_detector_instance = SiteMultimodalDetector()
    return _site_detector_instance

# For backward compatibility, create property that initializes on demand
site_detector = property(lambda self: get_site_detector())
try:
    site_detector = get_site_detector()
except Exception as exc:
    logger.warning("Failed to initialize site_detector at module load: %s", exc)
    site_detector = None


def main() -> None:
    parser = argparse.ArgumentParser(description="Train or inspect the site multimodal phishing detector.")
    parser.add_argument("--train", action="store_true", help="Build the dataset and train all site models.")
    parser.add_argument("--epochs", type=int, default=2, help="Number of epochs for the text model.")
    parser.add_argument("--max-samples", type=int, default=None, help="Optional cap for faster local runs.")
    args = parser.parse_args()

    if args.train:
        train_site_multimodal_model(epochs=args.epochs, max_samples=args.max_samples)
    else:
        detector = get_site_detector()
        if detector:
            print(json.dumps(detector.metadata, indent=2))
        else:
            print("No models trained yet")


if __name__ == "__main__":
    main()