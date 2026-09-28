# ============================================================
# api.py
#
# FACE ATTENDANCE FASTAPI BACKEND
#
# FUNCTIONS
#
# REGISTER
#     ↓
# Save 10 train images
# Save 5 test images
#     ↓
# Train YOLO
#     ↓
# Save employee information
#
# ATTENDANCE
#     ↓
# Receive Employee ID + Image
#     ↓
# record.py
#     ↓
# predict.py
#     ↓
# Compare registered name with predicted name
#     ↓
# Save attendance.csv
# ============================================================

import csv
import json
import random
import subprocess
import sys
import uuid

from pathlib import Path
from typing import List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException

# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(title="Face Attendance API")


# ============================================================
# BASE PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# DATASET PATHS
# ============================================================

DATASET_DIR = BASE_DIR / "datasets"

TRAIN_DIR = DATASET_DIR / "train"

TEST_DIR = DATASET_DIR / "test"


# ============================================================
# OUTPUT PATH
# ============================================================

OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# EMPLOYEE FILE
# ============================================================

EMPLOYEES_FILE = OUTPUT_DIR / "employees.csv"


# ============================================================
# RUNTIME PATHS
# ============================================================

RUNS_DIR = BASE_DIR / "runs"

ATTENDANCE_IMAGES_DIR = RUNS_DIR / "attendance_images"


# ============================================================
# PYTHON SCRIPTS
# ============================================================

RECORD_SCRIPT = BASE_DIR / "record.py"

TRAIN_SCRIPT = BASE_DIR / "train.py"


# ============================================================
# CREATE DIRECTORIES
# ============================================================

TRAIN_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

TEST_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

ATTENDANCE_IMAGES_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# ALLOWED IMAGE EXTENSIONS
# ============================================================

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


# ============================================================
# HEALTH CHECK
# ============================================================


@app.get("/")
async def root():

    return {
        "status": "running",
        "service": "Face Attendance API",
    }


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
        .casefold()
        .replace("_", "")
        .replace("-", "")
        .replace(" ", "")
        .replace("(", "")
        .replace(")", "")
    )


# ============================================================
# READ TEXT FILE
#
# Supports common Windows encodings.
# ============================================================


def read_text_file(file_path):

    encodings = [
        "utf-8-sig",
        "utf-8",
        "utf-16",
        "cp1252",
    ]

    for encoding in encodings:

        try:

            with open(
                file_path,
                "r",
                encoding=encoding,
                newline="",
            ) as file:

                return file.read()

        except UnicodeDecodeError:

            continue

        except Exception:

            return None

    return None


# ============================================================
# GET ALL EMPLOYEES
# ============================================================


def get_all_employees():

    employees = []

    if not EMPLOYEES_FILE.exists():

        return employees

    content = read_text_file(EMPLOYEES_FILE)

    if content is None:

        return employees

    content = content.strip()

    if not content:

        return employees

    lines = [line for line in content.splitlines() if line.strip()]

    if len(lines) < 2:

        return employees

    # --------------------------------------------------------
    # Detect delimiter
    # --------------------------------------------------------

    header_line = lines[0]

    if "\t" in header_line:

        delimiter = "\t"

    elif "," in header_line:

        delimiter = ","

    elif ";" in header_line:

        delimiter = ";"

    elif "|" in header_line:

        delimiter = "|"

    else:

        delimiter = ","

    # --------------------------------------------------------
    # CSV reader
    # --------------------------------------------------------

    try:

        reader = csv.DictReader(
            lines,
            delimiter=delimiter,
        )

        for row in reader:

            employee_id = ""

            name = ""

            for key, value in row.items():

                normalized = normalize_header(key)

                if normalized in {
                    "employeeid",
                    "empid",
                }:

                    employee_id = str(value or "").strip()

                elif normalized in {
                    "name",
                    "employeename",
                }:

                    name = str(value or "").strip()

            if employee_id and name:

                employees.append(
                    {
                        "employee_id": employee_id,
                        "name": name,
                    }
                )

    except Exception as error:

        print(
            "Error reading employees.csv:",
            error,
        )

    return employees


# ============================================================
# FIND EMPLOYEE
# ============================================================


def find_employee(employee_id):

    search_id = str(employee_id).strip().casefold()

    employees = get_all_employees()

    for employee in employees:

        current_id = employee["employee_id"].strip().casefold()

        if current_id == search_id:

            return employee

    return None


# ============================================================
# SAVE EMPLOYEE
#
# IMPORTANT:
# Existing employees are preserved.
# ============================================================


def save_employee(
    employee_id,
    name,
):

    employees = get_all_employees()

    # --------------------------------------------------------
    # Check whether employee already exists
    # --------------------------------------------------------

    for employee in employees:

        if employee["employee_id"].strip().casefold() == employee_id.strip().casefold():

            employee["name"] = name

            break

    else:

        employees.append(
            {
                "employee_id": employee_id,
                "name": name,
            }
        )

    # --------------------------------------------------------
    # Write employees.csv
    # --------------------------------------------------------

    with open(
        EMPLOYEES_FILE,
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "EMP-ID",
                "Name",
            ],
        )

        writer.writeheader()

        for employee in employees:

            writer.writerow(
                {
                    "EMP-ID": employee["employee_id"],
                    "Name": employee["name"],
                }
            )


# ============================================================
# RUN PYTHON SUBPROCESS
#
# IMPORTANT WINDOWS FIX:
#
# encoding="utf-8"
# errors="replace"
#
# This prevents:
#
# UnicodeDecodeError:
# 'charmap' codec can't decode byte...
# ============================================================


def run_python_process(
    command,
    timeout=None,
):

    try:

        result = subprocess.run(
            command,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )

        return result

    except subprocess.TimeoutExpired:

        raise

    except Exception:

        raise


# ============================================================
# REGISTER PERSON
# ============================================================


@app.post("/register")
async def register_person(
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
            detail="Name cannot be empty",
        )

    # ========================================================
    # VALIDATE EMPLOYEE ID
    # ========================================================

    if not employee_id:

        raise HTTPException(
            status_code=400,
            detail="Employee ID cannot be empty",
        )

    # ========================================================
    # VALIDATE IMAGE COUNT
    # ========================================================

    if len(images) < 15:

        raise HTTPException(
            status_code=400,
            detail="At least 15 images are required",
        )

    # ========================================================
    # VALIDATE IMAGE TYPES
    # ========================================================

    valid_images = []

    for image in images:

        extension = Path(image.filename or "").suffix.lower()

        if extension in ALLOWED_EXTENSIONS:

            valid_images.append(image)

    if len(valid_images) < 15:

        raise HTTPException(
            status_code=400,
            detail=("At least 15 valid JPG, " "JPEG or PNG images are required"),
        )

    # ========================================================
    # CHECK EXISTING EMPLOYEE ID
    # ========================================================

    existing_employee = find_employee(employee_id)

    if existing_employee is not None:

        raise HTTPException(
            status_code=400,
            detail=(f"Employee ID '{employee_id}' " "is already registered."),
        )

    # ========================================================
    # CREATE CLASS FOLDERS
    # ========================================================

    train_person_dir = TRAIN_DIR / name

    test_person_dir = TEST_DIR / name

    train_person_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    test_person_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # SELECT 15 IMAGES
    # ========================================================

    selected_images = random.sample(
        valid_images,
        15,
    )

    # ========================================================
    # SELECT 5 TEST IMAGES
    # ========================================================

    test_images = random.sample(
        selected_images,
        5,
    )

    # ========================================================
    # REMAINING 10 = TRAIN
    # ========================================================

    train_images = [image for image in selected_images if image not in test_images]

    # ========================================================
    # SAVE TRAIN IMAGES
    # ========================================================

    train_count = 0

    for index, image in enumerate(
        train_images,
        start=1,
    ):

        extension = Path(image.filename or "").suffix.lower()

        file_path = train_person_dir / f"{index:03d}{extension}"

        contents = await image.read()

        with open(
            file_path,
            "wb",
        ) as file:

            file.write(contents)

        train_count += 1

    # ========================================================
    # SAVE TEST IMAGES
    # ========================================================

    test_count = 0

    for index, image in enumerate(
        test_images,
        start=1,
    ):

        extension = Path(image.filename or "").suffix.lower()

        file_path = test_person_dir / f"{index:03d}{extension}"

        contents = await image.read()

        with open(
            file_path,
            "wb",
        ) as file:

            file.write(contents)

        test_count += 1

    # ========================================================
    # SAVE EMPLOYEE
    #
    # Save before training so the employee is available
    # immediately after successful registration.
    # ========================================================

    try:

        save_employee(
            employee_id,
            name,
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Images were saved, but "
                "employees.csv could not be updated: "
                f"{error}"
            ),
        )

    # ========================================================
    # TRAIN YOLO
    # ========================================================

    if not TRAIN_SCRIPT.exists():

        raise HTTPException(
            status_code=500,
            detail="train.py not found",
        )

    print()
    print("=" * 70)
    print(f"STARTING YOLO TRAINING FOR {name}")
    print("=" * 70)

    try:

        training_result = run_python_process(
            [
                sys.executable,
                str(TRAIN_SCRIPT),
            ],
            timeout=3600,
        )

    except subprocess.TimeoutExpired:

        raise HTTPException(
            status_code=500,
            detail=("YOLO training timed out. " "Please check the training terminal."),
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=("Unable to start YOLO training: " f"{error}"),
        )

    # ========================================================
    # PRINT TRAINING OUTPUT
    # ========================================================

    print()
    print("=" * 70)
    print("TRAIN.PY OUTPUT")
    print("=" * 70)

    if training_result.stdout:

        print(training_result.stdout)

    if training_result.stderr:

        print()
        print("TRAIN.PY STDERR")

        print(training_result.stderr)

    # ========================================================
    # TRAINING FAILED
    # ========================================================

    if training_result.returncode != 0:

        raise HTTPException(
            status_code=500,
            detail=(
                "YOLO training failed. "
                "Check the FastAPI terminal "
                "for training details."
            ),
        )

    # ========================================================
    # SUCCESS
    # ========================================================

    return {
        "status": "success",
        "message": (f"{name} registered successfully " "and YOLO training completed."),
        "name": name,
        "employee_id": employee_id,
        "train_images": train_count,
        "test_images": test_count,
        "train_path": str(train_person_dir),
        "test_path": str(test_person_dir),
        "employees_file": str(EMPLOYEES_FILE),
    }


# ============================================================
# RECORD ATTENDANCE
#
# Streamlit
#     ↓
# FastAPI
#     ↓
# record.py
#     ↓
# predict.py
#     ↓
# attendance.csv
# ============================================================


@app.post("/record-attendance")
async def record_attendance(
    emp_id: str = Form(...),
    image: UploadFile = File(...),
):

    # ========================================================
    # VALIDATE EMPLOYEE ID
    # ========================================================

    emp_id = emp_id.strip()

    if not emp_id:

        raise HTTPException(
            status_code=400,
            detail="Employee ID is required",
        )

    # ========================================================
    # VALIDATE EMPLOYEE
    # ========================================================

    employee = find_employee(emp_id)

    if employee is None:

        raise HTTPException(
            status_code=404,
            detail=(f"Employee ID '{emp_id}' " "is not registered."),
        )

    # ========================================================
    # VALIDATE IMAGE
    # ========================================================

    if not image.filename:

        raise HTTPException(
            status_code=400,
            detail="Image is required",
        )

    extension = Path(image.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail=("Only JPG, JPEG and PNG " "images are allowed"),
        )

    # ========================================================
    # CHECK record.py
    # ========================================================

    if not RECORD_SCRIPT.exists():

        raise HTTPException(
            status_code=500,
            detail="record.py not found",
        )

    # ========================================================
    # CREATE TEMPORARY IMAGE
    # ========================================================

    unique_name = f"{uuid.uuid4().hex}" f"{extension}"

    image_path = ATTENDANCE_IMAGES_DIR / unique_name

    try:

        contents = await image.read()

        with open(
            image_path,
            "wb",
        ) as file:

            file.write(contents)

        # ====================================================
        # CALL record.py
        #
        # UTF-8 fix is also applied here.
        # ====================================================

        result = run_python_process(
            [
                sys.executable,
                str(RECORD_SCRIPT),
                emp_id,
                str(image_path),
            ],
            timeout=180,
        )

        # ====================================================
        # PRINT record.py OUTPUT
        # ====================================================

        print()
        print("=" * 70)
        print("RECORD.PY OUTPUT")
        print("=" * 70)

        if result.stdout:

            print(result.stdout)

        if result.stderr:

            print()
            print("RECORD.PY STDERR")

            print(result.stderr)

        # ====================================================
        # PROCESS ERROR
        # ====================================================

        if result.returncode != 0:

            return {
                "success": False,
                "message": (
                    "Sorry, we couldn't " "recognize you. " "Please try again."
                ),
            }

        # ====================================================
        # READ JSON RESULT
        #
        # record.py prints JSON on stdout.
        # Search from bottom to top.
        # ====================================================

        json_result = None

        for line in reversed(result.stdout.splitlines()):

            line = line.strip()

            if not line:

                continue

            try:

                parsed = json.loads(line)

                if isinstance(
                    parsed,
                    dict,
                ):

                    json_result = parsed

                    break

            except json.JSONDecodeError:

                continue

        # ====================================================
        # JSON NOT FOUND
        # ====================================================

        if json_result is None:

            return {
                "success": False,
                "message": (
                    "Sorry, we couldn't " "recognize you. " "Please try again."
                ),
            }

        # ====================================================
        # RETURN record.py RESULT
        # ====================================================

        return json_result

    except subprocess.TimeoutExpired:

        return {
            "success": False,
            "message": ("Recognition timed out. " "Please try again."),
        }

    except Exception as error:

        print(
            "Attendance API error:",
            str(error),
        )

        return {
            "success": False,
            "message": ("Sorry, we couldn't " "recognize you. " "Please try again."),
        }

    finally:

        # ====================================================
        # DELETE TEMP IMAGE
        # ====================================================

        try:

            if image_path.exists():

                image_path.unlink()

        except Exception:

            pass


# ============================================================
# GET EMPLOYEES
#
# Used by Streamlit dashboard.
# ============================================================


@app.get("/employees")
async def get_employees():

    employees = get_all_employees()

    return {
        "success": True,
        "count": len(employees),
        "employees": employees,
    }
