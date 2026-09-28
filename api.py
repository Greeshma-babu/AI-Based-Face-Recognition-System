# ============================================================
# api.py
#
# FaceMark Attendance FastAPI Backend
#
# REGISTRATION
#   Streamlit
#       ↓
#   /register
#       ↓
#   datasets/train/<name>
#   datasets/test/<name>
#       ↓
#   train.py
#       ↓
#   BACKGROUND TRAINING
#
# ATTENDANCE
#   Streamlit
#       ↓
#   /record
#       ↓
#   record.py
#       ↓
#   predict.py
#       ↓
#   YOLO
#       ↓
#   attendance.csv
# ============================================================

import csv
import json
import random
import shutil
import subprocess
import sys
import tempfile

from pathlib import Path
from typing import List

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)

# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="FaceMark Attendance API",
    version="1.0.0",
)


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# DIRECTORIES
# ============================================================

DATASET_DIR = BASE_DIR / "datasets"

TRAIN_DIR = DATASET_DIR / "train"

TEST_DIR = DATASET_DIR / "test"

OUTPUT_DIR = BASE_DIR / "output"


# ============================================================
# FILES
# ============================================================

EMPLOYEES_FILE = OUTPUT_DIR / "employees.csv"

ATTENDANCE_FILE = OUTPUT_DIR / "attendance.csv"

RECORD_FILE = BASE_DIR / "record.py"

TRAIN_SCRIPT = BASE_DIR / "train.py"

TRAINING_LOG = OUTPUT_DIR / "training.log"


# ============================================================
# CSV HEADERS
# ============================================================

EMPLOYEE_HEADERS = [
    "employee_id",
    "name",
]


# ============================================================
# CREATE DIRECTORIES
# ============================================================

DATASET_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

TRAIN_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

TEST_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# NORMALIZE CSV HEADER
# ============================================================


def normalize_header(value):

    if value is None:
        return ""

    return (
        str(value)
        .replace("\ufeff", "")
        .strip()
        .lower()
        .replace(" ", "")
        .replace("_", "")
        .replace("-", "")
    )


# ============================================================
# DETECT CSV DELIMITER
# ============================================================


def detect_delimiter(line):

    if "\t" in line:
        return "\t"

    if ";" in line:
        return ";"

    if "|" in line:
        return "|"

    if "," in line:
        return ","

    return ","


# ============================================================
# READ EMPLOYEES CSV
# ============================================================


def read_employees_file():

    if not EMPLOYEES_FILE.exists():
        return []

    encodings = [
        "utf-8-sig",
        "utf-8",
        "utf-16",
        "cp1252",
    ]

    content = None

    for encoding in encodings:

        try:

            with open(
                EMPLOYEES_FILE,
                "r",
                encoding=encoding,
                newline="",
            ) as file:

                content = file.read()

            break

        except UnicodeDecodeError:

            continue

        except Exception as error:

            print(
                "Error reading employees.csv:",
                error,
            )

            return []

    if content is None:
        return []

    content = content.strip()

    if not content:
        return []

    lines = content.splitlines()

    if not lines:
        return []

    delimiter = detect_delimiter(lines[0])

    try:

        reader = csv.reader(
            lines,
            delimiter=delimiter,
        )

        rows = list(reader)

    except Exception as error:

        print(
            "CSV parsing error:",
            error,
        )

        return []

    if not rows:
        return []

    header = [normalize_header(column) for column in rows[0]]

    employee_id_index = None

    name_index = None

    for index, column in enumerate(header):

        if column in {
            "employeeid",
            "empid",
        }:

            employee_id_index = index

        if column in {
            "name",
            "employeename",
        }:

            name_index = index

    # ========================================================
    # FALLBACK
    # ========================================================

    if employee_id_index is None:
        employee_id_index = 0

    if name_index is None:
        name_index = 1

    employees = []

    for row in rows[1:]:

        if len(row) <= max(
            employee_id_index,
            name_index,
        ):
            continue

        employee_id = str(row[employee_id_index]).strip()

        name = str(row[name_index]).strip()

        if not employee_id or not name:
            continue

        employees.append(
            {
                "employee_id": employee_id,
                "name": name,
            }
        )

    return employees


# ============================================================
# ENSURE EMPLOYEES CSV
# ============================================================


def ensure_employees_file():

    if not EMPLOYEES_FILE.exists():

        with open(
            EMPLOYEES_FILE,
            "w",
            newline="",
            encoding="utf-8",
        ) as file:

            writer = csv.writer(file)

            writer.writerow(EMPLOYEE_HEADERS)

    employees = read_employees_file()

    print()
    print("=" * 70)
    print("EMPLOYEES CSV")
    print("=" * 70)

    print(
        "File:",
        EMPLOYEES_FILE,
    )

    print(
        "Employees found:",
        len(employees),
    )

    for employee in employees:

        print(f"  {employee['employee_id']} -> " f"{employee['name']}")

    print("=" * 70)
    print()


# ============================================================
# FIND EMPLOYEE
# ============================================================


def find_employee(employee_id):

    employee_id = str(employee_id).strip().lower()

    employees = read_employees_file()

    for employee in employees:

        current_id = employee["employee_id"].strip().lower()

        if current_id == employee_id:

            return employee

    return None


# ============================================================
# SAVE EMPLOYEE
# ============================================================


def save_employee(
    employee_id,
    name,
):

    employees = read_employees_file()

    employees.append(
        {
            "employee_id": employee_id.strip(),
            "name": name.strip(),
        }
    )

    with open(
        EMPLOYEES_FILE,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=EMPLOYEE_HEADERS,
        )

        writer.writeheader()

        writer.writerows(employees)


# ============================================================
# REMOVE EMPLOYEE
# ============================================================


def remove_employee(employee_id):

    employee_id = employee_id.strip().lower()

    employees = read_employees_file()

    remaining = [
        employee
        for employee in employees
        if (employee["employee_id"].strip().lower() != employee_id)
    ]

    with open(
        EMPLOYEES_FILE,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=EMPLOYEE_HEADERS,
        )

        writer.writeheader()

        writer.writerows(remaining)


# ============================================================
# SAFE PERSON NAME
# ============================================================


def safe_name(name):

    cleaned = "".join(
        character
        for character in name
        if (
            character.isalnum()
            or character
            in (
                " ",
                "_",
                "-",
            )
        )
    )

    cleaned = cleaned.strip()

    if not cleaned:

        raise HTTPException(
            status_code=400,
            detail="Invalid employee name.",
        )

    return cleaned


# ============================================================
# START BACKGROUND TRAINING
#
# IMPORTANT:
#
# This version DOES NOT use:
#
#     DETACHED_PROCESS
#
# and DOES NOT use:
#
#     stdout=DEVNULL
#     stderr=DEVNULL
#
# Instead:
#
#     train.py runs silently in the background
#     YOLO output goes to:
#
#     output/training.log
#
# ============================================================


def start_background_training():

    # ========================================================
    # CHECK TRAIN.PY
    # ========================================================

    if not TRAIN_SCRIPT.exists():

        raise FileNotFoundError(f"train.py not found:\n{TRAIN_SCRIPT}")

    print()
    print("=" * 70)
    print("STARTING YOLO TRAINING IN BACKGROUND")
    print("=" * 70)

    print(
        "Training script:",
        TRAIN_SCRIPT,
    )

    print(
        "Python executable:",
        sys.executable,
    )

    print(
        "Training log:",
        TRAINING_LOG,
    )

    # ========================================================
    # OPEN TRAINING LOG
    # ========================================================

    log_file = open(
        TRAINING_LOG,
        "a",
        encoding="utf-8",
        buffering=1,
    )

    # ========================================================
    # WRITE START INFORMATION
    # ========================================================

    log_file.write("\n")
    log_file.write("=" * 80 + "\n")
    log_file.write("YOLO TRAINING PROCESS STARTED\n")
    log_file.write("=" * 80 + "\n")

    log_file.write(f"Python: {sys.executable}\n")

    log_file.write(f"Script: {TRAIN_SCRIPT}\n")

    log_file.write(f"Working directory: {BASE_DIR}\n")

    log_file.flush()

    # ========================================================
    # WINDOWS
    # ========================================================

    if sys.platform.startswith("win"):

        creation_flags = subprocess.CREATE_NO_WINDOW

        process = subprocess.Popen(
            [
                sys.executable,
                "-u",
                str(TRAIN_SCRIPT),
            ],
            cwd=str(BASE_DIR),
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=creation_flags,
        )

    # ========================================================
    # LINUX / MAC
    # ========================================================

    else:

        process = subprocess.Popen(
            [
                sys.executable,
                "-u",
                str(TRAIN_SCRIPT),
            ],
            cwd=str(BASE_DIR),
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    # ========================================================
    # WRITE PID
    # ========================================================

    log_file.write(f"Background training PID: " f"{process.pid}\n")

    log_file.flush()

    print(
        "Background training PID:",
        process.pid,
    )

    print(
        "Training log:",
        TRAINING_LOG,
    )

    print("=" * 70)
    print("YOLO TRAINING PROCESS LAUNCHED")
    print("=" * 70)

    # ========================================================
    # DO NOT WAIT FOR TRAINING
    # ========================================================

    return process.pid


# ============================================================
# REGISTER
# ============================================================


@app.post("/register")
async def register(
    name: str = Form(...),
    employee_id: str = Form(...),
    images: List[UploadFile] = File(...),
):

    name = name.strip()

    employee_id = employee_id.strip()

    # ========================================================
    # VALIDATE NAME
    # ========================================================

    if not name:

        raise HTTPException(
            status_code=400,
            detail="Employee name is required.",
        )

    # ========================================================
    # VALIDATE EMPLOYEE ID
    # ========================================================

    if not employee_id:

        raise HTTPException(
            status_code=400,
            detail="Employee ID is required.",
        )

    # ========================================================
    # VALIDATE NUMBER OF IMAGES
    # ========================================================

    if len(images) < 15:

        raise HTTPException(
            status_code=400,
            detail=("At least 15 images are required. " f"Received {len(images)}."),
        )

    # ========================================================
    # CHECK DUPLICATE EMPLOYEE
    # ========================================================

    existing_employee = find_employee(employee_id)

    if existing_employee:

        raise HTTPException(
            status_code=400,
            detail=(f"Employee ID '{employee_id}' " "is already registered."),
        )

    # ========================================================
    # PERSON NAME
    # ========================================================

    person_name = safe_name(name)

    # ========================================================
    # DATASET DIRECTORIES
    # ========================================================

    train_person_dir = TRAIN_DIR / person_name

    test_person_dir = TEST_DIR / person_name

    # ========================================================
    # PREVENT DUPLICATE PERSON
    # ========================================================

    if train_person_dir.exists():

        raise HTTPException(
            status_code=400,
            detail=("Training folder already exists " f"for '{person_name}'."),
        )

    # ========================================================
    # VALID IMAGE EXTENSIONS
    # ========================================================

    valid_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
    }

    valid_images = []

    for image in images:

        if not image.filename:
            continue

        extension = Path(image.filename).suffix.lower()

        if extension in valid_extensions:

            valid_images.append(image)

    # ========================================================
    # CHECK VALID IMAGES
    # ========================================================

    if len(valid_images) < 15:

        raise HTTPException(
            status_code=400,
            detail=("At least 15 valid JPG, JPEG " "or PNG images are required."),
        )

    # ========================================================
    # RANDOMLY SELECT EXACTLY 15
    # ========================================================

    selected_images = random.sample(
        valid_images,
        15,
    )

    # ========================================================
    # RANDOMLY SELECT 5 TEST IMAGES
    # ========================================================

    test_images = random.sample(
        selected_images,
        5,
    )

    # ========================================================
    # REMAINING 10 TRAINING IMAGES
    # ========================================================

    train_images = [image for image in selected_images if image not in test_images]

    employee_saved = False

    try:

        # ====================================================
        # CREATE DIRECTORIES
        # ====================================================

        train_person_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        test_person_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ====================================================
        # SAVE TRAINING IMAGES
        # ====================================================

        for index, image in enumerate(
            train_images,
            start=1,
        ):

            extension = Path(image.filename).suffix.lower()

            destination = train_person_dir / f"{index:03d}{extension}"

            content = await image.read()

            with open(
                destination,
                "wb",
            ) as file:

                file.write(content)

        # ====================================================
        # SAVE TEST IMAGES
        # ====================================================

        for index, image in enumerate(
            test_images,
            start=1,
        ):

            extension = Path(image.filename).suffix.lower()

            destination = test_person_dir / f"{index:03d}{extension}"

            content = await image.read()

            with open(
                destination,
                "wb",
            ) as file:

                file.write(content)

        # ====================================================
        # SAVE EMPLOYEE
        # ====================================================

        save_employee(
            employee_id,
            name,
        )

        employee_saved = True

        # ====================================================
        # START BACKGROUND TRAINING
        # ====================================================

        print()
        print("=" * 70)

        print(f"STARTING BACKGROUND TRAINING FOR " f"{name}")

        print("=" * 70)

        print(
            "Train images:",
            len(train_images),
        )

        print(
            "Test images:",
            len(test_images),
        )

        training_pid = start_background_training()

        # ====================================================
        # RETURN IMMEDIATELY
        # ====================================================

        return {
            "success": True,
            "message": (
                "Registration completed successfully. "
                "YOLO training started in the background."
            ),
            "name": name,
            "employee_id": employee_id,
            "train_images": len(train_images),
            "test_images": len(test_images),
            "training": "started",
            "training_pid": training_pid,
            "training_log": str(TRAINING_LOG),
        }

    except HTTPException:

        raise

    except Exception as error:

        print()
        print("=" * 70)
        print("REGISTRATION ERROR")
        print("=" * 70)

        print(repr(error))

        # ====================================================
        # ROLLBACK EMPLOYEE
        # ====================================================

        if employee_saved:

            remove_employee(employee_id)

        # ====================================================
        # REMOVE TRAIN DIRECTORY
        # ====================================================

        if train_person_dir.exists():

            shutil.rmtree(
                train_person_dir,
                ignore_errors=True,
            )

        # ====================================================
        # REMOVE TEST DIRECTORY
        # ====================================================

        if test_person_dir.exists():

            shutil.rmtree(
                test_person_dir,
                ignore_errors=True,
            )

        raise HTTPException(
            status_code=500,
            detail=(f"Registration failed: " f"{error}"),
        )


# ============================================================
# RECORD ATTENDANCE
# ============================================================


@app.post("/record")
async def record_attendance(
    employee_id: str = Form(...),
    image: UploadFile = File(...),
):

    employee_id = employee_id.strip()

    print()
    print("=" * 70)
    print("ATTENDANCE REQUEST")
    print("=" * 70)

    print(
        "Employee ID:",
        employee_id,
    )

    print(
        "Employees file:",
        EMPLOYEES_FILE,
    )

    # ========================================================
    # FIND EMPLOYEE
    # ========================================================

    employee = find_employee(employee_id)

    print(
        "Employee lookup result:",
        employee,
    )

    if employee is None:

        raise HTTPException(
            status_code=404,
            detail=(f"Employee ID '{employee_id}' " "is not registered."),
        )

    print(
        "Registered employee:",
        employee["name"],
    )

    # ========================================================
    # VALIDATE IMAGE
    # ========================================================

    if not image.filename:

        raise HTTPException(
            status_code=400,
            detail="Attendance image is required.",
        )

    extension = Path(image.filename).suffix.lower()

    if extension not in {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".webp",
    }:

        extension = ".jpg"

    temporary_file = None

    try:

        # ====================================================
        # SAVE TEMPORARY IMAGE
        # ====================================================

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp:

            content = await image.read()

            temp.write(content)

            temporary_file = Path(temp.name)

        print(
            "Temporary image:",
            temporary_file,
        )

        # ====================================================
        # CHECK RECORD.PY
        # ====================================================

        if not RECORD_FILE.exists():

            raise HTTPException(
                status_code=500,
                detail="record.py not found.",
            )

        # ====================================================
        # RUN RECORD.PY
        #
        # record.py sends:
        #
        #   JSON -> stdout
        #   debug -> stderr
        #
        # So we can safely parse stdout.
        # ====================================================

        process = subprocess.run(
            [
                sys.executable,
                str(RECORD_FILE),
                employee_id,
                str(temporary_file),
            ],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )

        print(
            "record.py return code:",
            process.returncode,
        )

        print("record.py stdout:")

        print(process.stdout)

        print("record.py stderr:")

        print(process.stderr)

        # ====================================================
        # GET OUTPUT
        # ====================================================

        output = process.stdout.strip()

        if not output:

            raise HTTPException(
                status_code=500,
                detail=(process.stderr.strip() or "Attendance processing failed."),
            )

        # ====================================================
        # PARSE JSON
        # ====================================================

        result = None

        # ----------------------------------------------------
        # TRY COMPLETE OUTPUT
        # ----------------------------------------------------

        try:

            result = json.loads(output)

        except json.JSONDecodeError:

            pass

        # ----------------------------------------------------
        # SEARCH JSON FROM BOTTOM
        # ----------------------------------------------------

        if result is None:

            for line in reversed(output.splitlines()):

                line = line.strip()

                if not line:
                    continue

                if line.startswith("{") and line.endswith("}"):

                    try:

                        result = json.loads(line)

                        break

                    except json.JSONDecodeError:

                        continue

        # ====================================================
        # INVALID RESPONSE
        # ====================================================

        if result is None:

            raise HTTPException(
                status_code=500,
                detail=("Invalid response from " "record.py.\n\n" + output[-5000:]),
            )

        # ====================================================
        # RETURN RESULT
        # ====================================================

        return result

    except subprocess.TimeoutExpired:

        raise HTTPException(
            status_code=500,
            detail=("Attendance recognition " "timed out."),
        )

    except HTTPException:

        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(f"Attendance failed: " f"{error}"),
        )

    finally:

        # ====================================================
        # DELETE TEMP IMAGE
        # ====================================================

        if temporary_file is not None and temporary_file.exists():

            try:

                temporary_file.unlink()

            except Exception:

                pass


# ============================================================
# GET EMPLOYEES
# ============================================================


@app.get("/employees")
def employees():

    employee_list = read_employees_file()

    return {
        "success": True,
        "count": len(employee_list),
        "employees": employee_list,
        "employees_file": str(EMPLOYEES_FILE),
    }


# ============================================================
# TRAINING STATUS
#
# This endpoint does NOT interfere with training.
#
# Open:
#
# http://127.0.0.1:8000/training-status
#
# ============================================================


@app.get("/training-status")
def training_status():

    if not TRAINING_LOG.exists():

        return {
            "success": True,
            "status": "not_started",
            "message": ("Training has not started."),
            "training_log": str(TRAINING_LOG),
        }

    try:

        with open(
            TRAINING_LOG,
            "r",
            encoding="utf-8",
            errors="replace",
        ) as file:

            lines = file.readlines()

    except Exception as error:

        return {
            "success": False,
            "status": "error",
            "message": ("Unable to read training log."),
            "error": str(error),
        }

    # ========================================================
    # LAST 30 LINES
    # ========================================================

    last_lines = [line.rstrip() for line in lines[-30:]]

    full_text = "".join(lines)

    # ========================================================
    # DETERMINE STATUS
    # ========================================================

    if "TRAINING COMPLETED" in full_text:

        status = "completed"

    elif "TRAINING FAILED" in full_text:

        status = "failed"

    elif "YOLO TRAINING PROCESS STARTED" in full_text:

        status = "running"

    else:

        status = "started"

    return {
        "success": True,
        "status": status,
        "training_log": str(TRAINING_LOG),
        "last_lines": last_lines,
    }


# ============================================================
# HEALTH CHECK
# ============================================================


@app.get("/")
def root():

    return {
        "success": True,
        "message": ("FaceMark Attendance API " "is running."),
    }


# ============================================================
# INITIALIZE
# ============================================================

ensure_employees_file()
