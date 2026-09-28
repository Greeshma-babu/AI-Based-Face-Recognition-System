# ============================================================
# predict.py
#
# YOLO FACE/PERSON CLASSIFICATION PREDICTION
#
# Input:
#     image path
#
# Output:
#     JSON
# ============================================================

import json
import sys
from pathlib import Path

from ultralytics import YOLO

# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# MODEL
# ============================================================

MODEL_PATH = (
    BASE_DIR / "runs" / "classify" / "object_classification" / "weights" / "best.pt"
)


# ============================================================
# VALID IMAGE EXTENSIONS
# ============================================================

VALID_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}


# ============================================================
# JSON OUTPUT
# ============================================================


def output(data):

    # IMPORTANT:
    # record.py expects ONLY JSON on stdout.

    print(json.dumps(data))


# ============================================================
# VALIDATE MODEL
# ============================================================

if not MODEL_PATH.exists():

    output(
        {
            "success": False,
            "message": "YOLO model not found.",
            "model": str(MODEL_PATH),
        }
    )

    sys.exit(1)


# ============================================================
# GET IMAGE PATH
# ============================================================

if len(sys.argv) < 2:

    output(
        {
            "success": False,
            "message": "Image path was not provided.",
        }
    )

    sys.exit(1)


IMAGE_PATH = Path(sys.argv[1])


# ============================================================
# VALIDATE IMAGE
# ============================================================

if not IMAGE_PATH.exists():

    output(
        {
            "success": False,
            "message": "Image file not found.",
            "image": str(IMAGE_PATH),
        }
    )

    sys.exit(1)


if IMAGE_PATH.suffix.lower() not in VALID_EXTENSIONS:

    output(
        {
            "success": False,
            "message": "Unsupported image format.",
            "image": str(IMAGE_PATH),
        }
    )

    sys.exit(1)


# ============================================================
# LOAD MODEL
# ============================================================

try:

    model = YOLO(str(MODEL_PATH))

except Exception as e:

    output(
        {
            "success": False,
            "message": ("Unable to load YOLO model: " f"{str(e)}"),
        }
    )

    sys.exit(1)


# ============================================================
# RUN PREDICTION
# ============================================================

try:

    results = model(
        str(IMAGE_PATH),
        verbose=False,
    )

except Exception as e:

    output(
        {
            "success": False,
            "message": ("Prediction failed: " f"{str(e)}"),
        }
    )

    sys.exit(1)


# ============================================================
# VALIDATE RESULTS
# ============================================================

if not results:

    output(
        {
            "success": False,
            "message": "YOLO returned no prediction.",
        }
    )

    sys.exit(1)


result = results[0]


# ============================================================
# CHECK CLASSIFICATION
# ============================================================

if result.probs is None:

    output(
        {
            "success": False,
            "message": ("No classification " "probabilities returned."),
        }
    )

    sys.exit(1)


# ============================================================
# TOP CLASS
# ============================================================

top_class_id = int(result.probs.top1)

top_class_name = result.names[top_class_id]

top_confidence = float(result.probs.top1conf.item()) * 100


# ============================================================
# ALL CLASS CONFIDENCES
# ============================================================

all_predictions = {}

for class_id, confidence in enumerate(result.probs.data):

    class_name = result.names[class_id]

    all_predictions[class_name] = round(
        float(confidence.item()) * 100,
        2,
    )


# ============================================================
# OUTPUT
# ============================================================

output(
    {
        "success": True,
        "predicted_name": top_class_name,
        "confidence": round(
            top_confidence,
            2,
        ),
        "image": str(IMAGE_PATH),
        "all_predictions": all_predictions,
    }
)
