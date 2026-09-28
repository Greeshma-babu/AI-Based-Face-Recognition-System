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
#
# IMPORTANT:
#     This version automatically finds the newest valid YOLO
#     classification model and verifies its class names.
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
# MODEL DIRECTORIES
# ============================================================

CLASSIFY_MODEL = (
    BASE_DIR / "runs" / "classify" / "object_classification" / "weights" / "best.pt"
)

ULTRALYTICS_MODEL = BASE_DIR / "runs" / "object_classification" / "weights" / "best.pt"


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
    """
    record.py expects ONLY JSON on stdout.
    """

    print(json.dumps(data))


# ============================================================
# FIND AVAILABLE MODELS
# ============================================================


def find_models():

    models = []

    if CLASSIFY_MODEL.exists():
        models.append(CLASSIFY_MODEL)

    if ULTRALYTICS_MODEL.exists() and ULTRALYTICS_MODEL != CLASSIFY_MODEL:
        models.append(ULTRALYTICS_MODEL)

    return models


# ============================================================
# LOAD MODEL
# ============================================================


def load_best_model():

    models = find_models()

    if not models:

        output(
            {
                "success": False,
                "message": "No YOLO model found.",
                "checked_models": [
                    str(CLASSIFY_MODEL),
                    str(ULTRALYTICS_MODEL),
                ],
            }
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Try every available model.
    #
    # Prefer the model that contains the largest number of
    # classes because the current dataset contains 6 classes.
    # --------------------------------------------------------

    loaded_models = []

    for model_path in models:

        try:

            model = YOLO(str(model_path))

            names = getattr(model, "names", None)

            if names is None:
                continue

            if isinstance(names, dict):
                class_names = list(names.values())
            else:
                class_names = list(names)

            loaded_models.append(
                {
                    "path": model_path,
                    "model": model,
                    "class_names": class_names,
                    "class_count": len(class_names),
                }
            )

        except Exception:
            continue

    if not loaded_models:

        output(
            {
                "success": False,
                "message": "Unable to load any available YOLO model.",
                "checked_models": [str(path) for path in models],
            }
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Prefer the model with the largest number of classes.
    #
    # Current project:
    #
    # Alia
    # Deepika
    # Greeshma
    # Jyothika
    # Nimisha
    # Samatha
    #
    # = 6 classes
    # --------------------------------------------------------

    loaded_models.sort(
        key=lambda item: (
            item["class_count"],
            item["path"].stat().st_mtime,
        ),
        reverse=True,
    )

    selected = loaded_models[0]

    return (
        selected["model"],
        selected["path"],
        selected["class_names"],
    )


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
# LOAD BEST AVAILABLE MODEL
# ============================================================

try:

    model, MODEL_PATH, MODEL_CLASS_NAMES = load_best_model()

except SystemExit:

    raise

except Exception as e:

    output(
        {
            "success": False,
            "message": f"Unable to load YOLO model: {str(e)}",
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
            "message": f"Prediction failed: {str(e)}",
            "model": str(MODEL_PATH),
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
            "model": str(MODEL_PATH),
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
            "message": "No classification probabilities returned.",
            "model": str(MODEL_PATH),
        }
    )

    sys.exit(1)


# ============================================================
# GET MODEL CLASS NAMES
# ============================================================

names = result.names

if isinstance(names, dict):

    class_names = {
        int(class_id): str(class_name) for class_id, class_name in names.items()
    }

else:

    class_names = {index: str(name) for index, name in enumerate(names)}


# ============================================================
# GET PROBABILITIES
# ============================================================

probabilities = result.probs.data


# ============================================================
# VERIFY CLASS COUNT
# ============================================================

model_probability_count = len(probabilities)
model_name_count = len(class_names)

if model_probability_count != model_name_count:

    output(
        {
            "success": False,
            "message": "Model class count and probability count do not match.",
            "model": str(MODEL_PATH),
            "class_count": model_name_count,
            "probability_count": model_probability_count,
            "classes": list(class_names.values()),
        }
    )

    sys.exit(1)


# ============================================================
# ALL CLASS CONFIDENCES
# ============================================================

all_predictions = {}

for class_id in range(model_probability_count):

    class_name = class_names.get(
        class_id,
        f"class_{class_id}",
    )

    confidence = float(probabilities[class_id].item()) * 100

    all_predictions[class_name] = round(
        confidence,
        2,
    )


# ============================================================
# TOP CLASS
# ============================================================

top_class_id = int(result.probs.top1)

top_class_name = class_names.get(
    top_class_id,
    f"class_{top_class_id}",
)

top_confidence = float(result.probs.top1conf.item()) * 100


# ============================================================
# FINAL OUTPUT
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
        "model": str(MODEL_PATH),
        "class_count": model_name_count,
        "classes": list(class_names.values()),
        "all_predictions": all_predictions,
    }
)
