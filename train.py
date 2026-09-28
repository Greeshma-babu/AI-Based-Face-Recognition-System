# ============================================================
# train.py
#
# YOLO CLASSIFICATION TRAINING
#
# Dataset:
#
# datasets/
# ├── train/
# │   ├── Alia/
# │   ├── Deepika/
# │   ├── Greeshma/
# │   └── Jyothika/
# │
# └── test/
#     ├── Alia/
#     ├── Deepika/
#     ├── Greeshma/
#     └── Jyothika/
#
# Training:
#     Existing best.pt -> continue training
#
#     If no best.pt:
#     yolo11n-cls.pt -> initial training
# ============================================================

from pathlib import Path

from ultralytics import YOLO

# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# DATASET
# ============================================================

DATASET_DIR = BASE_DIR / "datasets"


# ============================================================
# EXISTING TRAINED MODEL
# ============================================================

EXISTING_MODEL = (
    BASE_DIR / "runs" / "classify" / "object_classification" / "weights" / "best.pt"
)


# ============================================================
# INITIAL MODEL
# ============================================================

INITIAL_MODEL = BASE_DIR / "yolo11n-cls.pt"


# ============================================================
# VALIDATE DATASET
# ============================================================

TRAIN_DIR = DATASET_DIR / "train"

TEST_DIR = DATASET_DIR / "test"


if not TRAIN_DIR.exists():

    raise FileNotFoundError(f"Training directory not found:\n{TRAIN_DIR}")


if not TEST_DIR.exists():

    raise FileNotFoundError(f"Testing directory not found:\n{TEST_DIR}")


# ============================================================
# FIND TRAINING CLASSES
# ============================================================

classes = sorted([folder.name for folder in TRAIN_DIR.iterdir() if folder.is_dir()])


if not classes:

    raise RuntimeError("No person folders found in datasets/train.")


print("=" * 70)
print("YOLO FACE CLASSIFICATION TRAINING")
print("=" * 70)

print(f"Number of classes: {len(classes)}")

print("Classes:")

for class_name in classes:

    print(f"  - {class_name}")


# ============================================================
# CHECK INITIAL MODEL
# ============================================================

if not EXISTING_MODEL.exists() and not INITIAL_MODEL.exists():

    raise FileNotFoundError(
        "Neither the existing YOLO model nor "
        "the initial YOLO model was found.\n\n"
        f"Expected initial model:\n{INITIAL_MODEL}"
    )


# ============================================================
# SELECT MODEL
# ============================================================

if EXISTING_MODEL.exists():

    print("=" * 70)
    print("EXISTING MODEL FOUND")
    print("=" * 70)

    print(f"Loading existing model:\n" f"{EXISTING_MODEL}")

    MODEL_PATH = EXISTING_MODEL

else:

    print("=" * 70)
    print("NO EXISTING MODEL FOUND")
    print("=" * 70)

    print(f"Loading initial model:\n" f"{INITIAL_MODEL}")

    MODEL_PATH = INITIAL_MODEL


# ============================================================
# LOAD MODEL
# ============================================================

print("=" * 70)
print("LOADING YOLO MODEL")
print("=" * 70)

model = YOLO(str(MODEL_PATH))


# ============================================================
# TRAIN
# ============================================================

print("=" * 70)
print("STARTING YOLO CLASSIFICATION TRAINING")
print("=" * 70)

print(f"Dataset:\n{DATASET_DIR}")

print(f"Model:\n{MODEL_PATH}")

print(f"Epochs: 20")

print(f"Image size: 224")

print(f"Batch size: 8")


model.train(
    data=str(DATASET_DIR),
    epochs=20,
    imgsz=224,
    batch=8,
    project=str(BASE_DIR / "runs"),
    name="object_classification",
    exist_ok=True,
)


# ============================================================
# COMPLETED
# ============================================================

BEST_MODEL = (
    BASE_DIR / "runs" / "classify" / "object_classification" / "weights" / "best.pt"
)


print("=" * 70)
print("TRAINING COMPLETED")
print("=" * 70)

print(f"Best model:\n{BEST_MODEL}")

if BEST_MODEL.exists():

    print("Model file verified successfully.")

else:

    print("WARNING: best.pt was not found.")
