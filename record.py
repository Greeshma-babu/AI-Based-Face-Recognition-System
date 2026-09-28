# ============================================================
# record.py
#
# FACE ATTENDANCE RECOGNITION CONTROLLER
#
# FLOW
#
# Employee ID
#      ↓
# output/employees.csv
#      ↓
# Get registered name
#      ↓
# Save current image
#      ↓
# output/tempImage/current_image.jpg
#      ↓
# predict.py
#      ↓
# YOLO predicts class/name
#      ↓
# Compare registered name with predicted name
#      ↓
# MATCH
#      ↓
# Save attendance
#
# ============================================================

import csv
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# FILES
# ============================================================

EMPLOYEES_FILE = OUTPUT_DIR / "employees.csv"

ATTENDANCE_FILE = OUTPUT_DIR / "attendance.csv"

PREDICT_FILE = BASE_DIR / "predict.py"


# ============================================================
# TEMPORARY IMAGE DIRECTORY
# ============================================================

TEMP_IMAGE_DIR = OUTPUT_DIR / "tempImage"

TEMP_IMAGE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# CURRENT ATTENDANCE IMAGE
# ============================================================

CURRENT_IMAGE_FILE = TEMP_IMAGE_DIR / "current_image.jpg"


# ============================================================
# STANDARD ATTENDANCE HEADERS
# ============================================================

DATE_HEADER = "Date (DD-MM-YYYY)"

TOTAL_HEADER = "Total Attendance"


# ============================================================
# JSON OUTPUT
# ============================================================


def print_json(data):

    print(
        json.dumps(
            data,
            ensure_ascii=False,
        )
    )


# ============================================================
# DEBUG OUTPUT
#
# IMPORTANT:
# Debug information goes to STDERR.
# JSON response goes only to STDOUT.
# This prevents api.py JSON parsing problems.
# ============================================================


def debug(message):

    print(
        message,
        file=sys.stderr,
    )


# ============================================================
# NORMALIZE HEADER
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
# DETECT DELIMITER
# ============================================================


def detect_delimiter(line):

    if "\t" in line:
        return "\t"

    if "," in line:
        return ","

    if ";" in line:
        return ";"

    if "|" in line:
        return "|"

    return ","


# ============================================================
# READ TEXT FILE
#
# Supports:
#   UTF-8
#   UTF-8 BOM
#   UTF-16
#   CP1252
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
# FIND EMPLOYEE
# ============================================================


def find_employee(employee_id):

    if not EMPLOYEES_FILE.exists():

        debug(f"Employees file not found: " f"{EMPLOYEES_FILE}")

        return None

    search_id = str(employee_id).strip().casefold()

    content = read_text_file(EMPLOYEES_FILE)

    if content is None:

        debug("Unable to read employees.csv")

        return None

    content = content.strip()

    if not content:

        return None

    lines = [line.strip() for line in content.splitlines() if line.strip()]

    if len(lines) < 2:

        return None

    # ========================================================
    # HEADER
    # ========================================================

    header_line = lines[0]

    delimiter = detect_delimiter(header_line)

    headers = [item.strip() for item in header_line.split(delimiter)]

    # ========================================================
    # FIND EMPLOYEE ID COLUMN
    # ========================================================

    employee_id_index = None

    for index, header in enumerate(headers):

        normalized = normalize_header(header)

        if normalized in {
            "employeeid",
            "empid",
        }:

            employee_id_index = index

            break

    # ========================================================
    # FIND NAME COLUMN
    # ========================================================

    name_index = None

    for index, header in enumerate(headers):

        normalized = normalize_header(header)

        if normalized in {
            "name",
            "employeename",
        }:

            name_index = index

            break

    # ========================================================
    # FALLBACK
    # ========================================================

    if employee_id_index is None:

        employee_id_index = 0

    if name_index is None:

        name_index = 1

    # ========================================================
    # READ EMPLOYEES
    # ========================================================

    for line in lines[1:]:

        values = [value.strip() for value in line.split(delimiter)]

        if len(values) < 2:
            continue

        if employee_id_index >= len(values):
            continue

        if name_index >= len(values):
            continue

        current_id = values[employee_id_index].strip()

        current_name = values[name_index].strip()

        if not current_id:
            continue

        if not current_name:
            continue

        if current_id.casefold() == search_id:

            return {
                "employee_id": current_id,
                "name": current_name,
            }

    return None


# ============================================================
# GET ALL EMPLOYEE IDS
# ============================================================


def get_all_employee_ids():

    employee_ids = []

    if not EMPLOYEES_FILE.exists():
        return employee_ids

    content = read_text_file(EMPLOYEES_FILE)

    if content is None:
        return employee_ids

    lines = [line.strip() for line in content.splitlines() if line.strip()]

    if len(lines) < 2:
        return employee_ids

    delimiter = detect_delimiter(lines[0])

    headers = [item.strip() for item in lines[0].split(delimiter)]

    employee_id_index = None

    for index, header in enumerate(headers):

        normalized = normalize_header(header)

        if normalized in {
            "employeeid",
            "empid",
        }:

            employee_id_index = index

            break

    if employee_id_index is None:

        employee_id_index = 0

    for line in lines[1:]:

        values = [value.strip() for value in line.split(delimiter)]

        if employee_id_index >= len(values):
            continue

        employee_id = values[employee_id_index].strip()

        if employee_id:

            employee_ids.append(employee_id)

    return employee_ids


# ============================================================
# READ ATTENDANCE FILE
# ============================================================


def read_attendance_file():

    if not ATTENDANCE_FILE.exists():

        return (
            [],
            [],
            ",",
        )

    content = read_text_file(ATTENDANCE_FILE)

    if content is None:

        return (
            [],
            [],
            ",",
        )

    content = content.strip()

    if not content:

        return (
            [],
            [],
            ",",
        )

    lines = [line for line in content.splitlines() if line.strip()]

    if not lines:

        return (
            [],
            [],
            ",",
        )

    delimiter = detect_delimiter(lines[0])

    try:

        reader = csv.DictReader(
            lines,
            delimiter=delimiter,
        )

        headers = []

        if reader.fieldnames:

            headers = [
                str(header).strip()
                for header in reader.fieldnames
                if header is not None
            ]

        rows = []

        for row in reader:

            clean_row = {}

            has_data = False

            for header in headers:

                value = str(row.get(header) or "").strip()

                clean_row[header] = value

                if value:
                    has_data = True

            # Ignore completely blank rows
            if has_data:

                rows.append(clean_row)

        return (
            headers,
            rows,
            delimiter,
        )

    except Exception as error:

        debug("Error reading attendance.csv: " + str(error))

        return (
            [],
            [],
            ",",
        )


# ============================================================
# FIND DATE COLUMN
# ============================================================


def find_date_column(headers):

    for header in headers:

        normalized = normalize_header(header)

        if normalized in {
            "date",
            "dateddmmyyyy",
        }:

            return header

    return None


# ============================================================
# FIND TOTAL COLUMN
# ============================================================


def find_total_column(headers):

    for header in headers:

        normalized = normalize_header(header)

        if normalized in {
            "totalattendance",
            "total",
        }:

            return header

    return None


# ============================================================
# FIND EMPLOYEE COLUMN
# ============================================================


def find_employee_column(
    headers,
    employee_id,
):

    search_id = str(employee_id).strip().casefold()

    for header in headers:

        if str(header).strip().casefold() == search_id:

            return header

    return None


# ============================================================
# CHECK DUPLICATE ATTENDANCE
# ============================================================


def already_attended_today(employee_id):

    headers, rows, _ = read_attendance_file()

    if not headers:
        return False

    date_column = find_date_column(headers)

    employee_column = find_employee_column(
        headers,
        employee_id,
    )

    if not date_column:
        return False

    if not employee_column:
        return False

    today = datetime.now().strftime("%d-%m-%Y")

    for row in rows:

        row_date = str(row.get(date_column) or "").strip()

        value = str(row.get(employee_column) or "").strip()

        if row_date == today and value == "1":

            return True

    return False


# ============================================================
# CREATE STANDARD ATTENDANCE HEADERS
# ============================================================


def create_attendance_headers():

    employee_ids = get_all_employee_ids()

    headers = [
        DATE_HEADER,
        TOTAL_HEADER,
    ]

    for employee_id in employee_ids:

        if employee_id not in headers:

            headers.append(employee_id)

    return headers


# ============================================================
# SAVE ATTENDANCE
# ============================================================


def save_attendance(employee_id):

    today = datetime.now().strftime("%d-%m-%Y")

    debug(f"Saving attendance for " f"{employee_id}")

    debug(f"Attendance file: " f"{ATTENDANCE_FILE}")

    # ========================================================
    # READ EXISTING FILE
    # ========================================================

    headers, rows, delimiter = read_attendance_file()

    # ========================================================
    # IF FILE DOES NOT EXIST OR IS INVALID
    # CREATE CLEAN STRUCTURE
    # ========================================================

    if not headers:

        headers = create_attendance_headers()

        delimiter = ","

        rows = []

        debug("Creating new attendance.csv")

    # ========================================================
    # FIND DATE COLUMN
    # ========================================================

    date_column = find_date_column(headers)

    if not date_column:

        raise ValueError("Date column not found " "in attendance.csv.")

    # ========================================================
    # FIND TOTAL COLUMN
    # ========================================================

    total_column = find_total_column(headers)

    if not total_column:

        raise ValueError("Total Attendance column " "not found in attendance.csv.")

    # ========================================================
    # FIND EMPLOYEE COLUMN
    # ========================================================

    employee_column = find_employee_column(
        headers,
        employee_id,
    )

    # ========================================================
    # IF EMPLOYEE COLUMN DOES NOT EXIST
    # ADD IT
    # ========================================================

    if not employee_column:

        employee_column = employee_id.strip()

        headers.append(employee_column)

        debug(f"Added missing employee " f"column: {employee_column}")

        # Add column to existing rows
        for row in rows:

            row[employee_column] = "0"

    # ========================================================
    # FIND TODAY'S ROW
    # ========================================================

    today_row = None

    for row in rows:

        row_date = str(row.get(date_column) or "").strip()

        if row_date == today:

            today_row = row

            break

    # ========================================================
    # CREATE TODAY'S ROW
    # ========================================================

    if today_row is None:

        debug(f"Creating attendance row " f"for {today}")

        today_row = {}

        for header in headers:

            today_row[header] = ""

        today_row[date_column] = today

        # ----------------------------------------------------
        # Set all employee columns to 0
        # ----------------------------------------------------

        for header in headers:

            normalized = normalize_header(header)

            if normalized.startswith("emp"):

                today_row[header] = "0"

        # ----------------------------------------------------
        # Mark current employee
        # ----------------------------------------------------

        today_row[employee_column] = "1"

        rows.append(today_row)

    # ========================================================
    # EXISTING TODAY ROW
    # ========================================================

    else:

        debug(f"Updating existing row " f"for {today}")

        today_row[employee_column] = "1"

    # ========================================================
    # RECALCULATE TOTAL ATTENDANCE
    # ========================================================

    total = 0

    for header in headers:

        normalized = normalize_header(header)

        if not normalized.startswith("emp"):
            continue

        value = str(today_row.get(header) or "").strip()

        if value == "1":

            total += 1

    today_row[total_column] = str(total)

    # ========================================================
    # REMOVE COMPLETELY BLANK ROWS
    # ========================================================

    clean_rows = []

    for row in rows:

        has_data = False

        for header in headers:

            value = str(row.get(header) or "").strip()

            if value:

                has_data = True

                break

        if has_data:

            clean_rows.append(row)

    rows = clean_rows

    # ========================================================
    # WRITE FILE
    # ========================================================

    try:

        with open(
            ATTENDANCE_FILE,
            "w",
            encoding="utf-8",
            newline="",
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=headers,
                delimiter=",",
                extrasaction="ignore",
            )

            writer.writeheader()

            writer.writerows(rows)

    except Exception as error:

        raise ValueError("Unable to write attendance.csv: " + str(error))

    # ========================================================
    # VERIFY FILE
    # ========================================================

    if not ATTENDANCE_FILE.exists():

        raise ValueError("attendance.csv was not created.")

    debug("Attendance saved successfully.")

    debug(f"Today's total attendance: " f"{total}")


# ============================================================
# COPY CURRENT IMAGE TO tempImage
# ============================================================


def prepare_current_image(image_path):

    try:

        source = Path(image_path)

        if not source.exists():

            return {
                "success": False,
                "message": ("Attendance image " "not found."),
            }

        # ----------------------------------------------------
        # Remove previous image
        # ----------------------------------------------------

        if CURRENT_IMAGE_FILE.exists():

            try:

                CURRENT_IMAGE_FILE.unlink()

            except Exception:

                pass

        # ----------------------------------------------------
        # Copy new image
        # ----------------------------------------------------

        shutil.copy2(
            source,
            CURRENT_IMAGE_FILE,
        )

        return {
            "success": True,
            "image": str(CURRENT_IMAGE_FILE),
        }

    except Exception as error:

        return {
            "success": False,
            "message": ("Unable to prepare " "attendance image."),
            "error": str(error),
        }


# ============================================================
# RUN PREDICTION
# ============================================================


def run_prediction(image_path):

    debug("Running predict.py...")

    debug(f"Prediction image: " f"{image_path}")

    try:

        process = subprocess.run(
            [
                sys.executable,
                str(PREDICT_FILE),
                str(image_path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )

    except subprocess.TimeoutExpired:

        return {
            "success": False,
            "message": ("Unable to recognize you. " "Please try again."),
        }

    except Exception as error:

        return {
            "success": False,
            "message": ("Unable to recognize you. " "Please try again."),
            "error": str(error),
        }

    # ========================================================
    # DEBUG PREDICT OUTPUT
    # ========================================================

    debug(f"predict.py return code: " f"{process.returncode}")

    if process.stdout.strip():

        debug("predict.py stdout:")

        debug(process.stdout.strip())

    if process.stderr.strip():

        debug("predict.py stderr:")

        debug(process.stderr.strip())

    # ========================================================
    # PREDICTION PROCESS FAILED
    # ========================================================

    if process.returncode != 0:

        return {
            "success": False,
            "message": ("Unable to recognize you. " "Please try again."),
            "error": (process.stderr.strip()),
        }

    output_text = process.stdout.strip()

    if not output_text:

        return {
            "success": False,
            "message": ("Unable to recognize you. " "Please try again."),
        }

    # ========================================================
    # FIND JSON
    #
    # predict.py should return JSON.
    # We search from bottom to top.
    # ========================================================

    for line in reversed(output_text.splitlines()):

        line = line.strip()

        if not line:
            continue

        try:

            result = json.loads(line)

            if isinstance(
                result,
                dict,
            ):

                return result

        except json.JSONDecodeError:

            continue

    # ========================================================
    # INVALID PREDICTION OUTPUT
    # ========================================================

    return {
        "success": False,
        "message": ("Unable to recognize you. " "Please try again."),
        "error": ("predict.py did not return " "valid JSON."),
    }


# ============================================================
# MAIN
# ============================================================


def main():

    # ========================================================
    # ARGUMENTS
    # ========================================================

    if len(sys.argv) < 3:

        print_json(
            {
                "success": False,
                "message": ("Employee ID and image " "are required."),
            }
        )

        sys.exit(1)

    employee_id = sys.argv[1].strip()

    image_path = Path(sys.argv[2]).resolve()

    # ========================================================
    # VALIDATE EMPLOYEE ID
    # ========================================================

    if not employee_id:

        print_json(
            {
                "success": False,
                "message": ("Employee ID is required."),
            }
        )

        sys.exit(0)

    # ========================================================
    # VALIDATE IMAGE
    # ========================================================

    if not image_path.exists():

        print_json(
            {
                "success": False,
                "message": ("Attendance image " "not found."),
                "image": str(image_path),
            }
        )

        sys.exit(0)

    # ========================================================
    # VALIDATE EMPLOYEE FILE
    # ========================================================

    if not EMPLOYEES_FILE.exists():

        print_json(
            {
                "success": False,
                "message": ("employees.csv could " "not be found."),
                "employees_file": str(EMPLOYEES_FILE),
            }
        )

        sys.exit(0)

    # ========================================================
    # DEBUG
    # ========================================================

    debug("=" * 70)

    debug("ATTENDANCE RECOGNITION")

    debug("=" * 70)

    debug(f"Employee ID   : {employee_id}")

    debug(f"Employees CSV : {EMPLOYEES_FILE}")

    debug(f"Attendance CSV : {ATTENDANCE_FILE}")

    debug(f"Input image   : {image_path}")

    debug(f"Temp image    : {CURRENT_IMAGE_FILE}")

    debug("=" * 70)

    # ========================================================
    # FIND EMPLOYEE
    # ========================================================

    employee = find_employee(employee_id)

    if employee is None:

        print_json(
            {
                "success": False,
                "message": (f"Employee ID " f"'{employee_id}' " "is not registered."),
                "employee_id": employee_id,
                "employees_file": str(EMPLOYEES_FILE),
            }
        )

        sys.exit(0)

    # ========================================================
    # REGISTERED NAME
    # ========================================================

    registered_name = employee["name"].strip()

    debug(f"Registered name: " f"{registered_name}")

    # ========================================================
    # SAVE IMAGE TO tempImage
    # ========================================================

    image_result = prepare_current_image(image_path)

    if not image_result.get(
        "success",
        False,
    ):

        print_json(
            {
                "success": False,
                "message": ("Unable to prepare " "attendance image."),
                "error": image_result.get(
                    "error",
                    "",
                ),
            }
        )

        sys.exit(0)

    # ========================================================
    # ALWAYS PREDICT USING CURRENT IMAGE
    # ========================================================

    prediction_image = CURRENT_IMAGE_FILE

    debug(f"Prediction image: " f"{prediction_image}")

    # ========================================================
    # RUN YOLO
    # ========================================================

    prediction = run_prediction(prediction_image)

    # ========================================================
    # PREDICTION FAILED
    # ========================================================

    if not prediction.get(
        "success",
        False,
    ):

        print_json(
            {
                "success": False,
                "message": ("Unable to recognize you. " "Please try again."),
                "employee_id": employee_id,
                "registered_name": (registered_name),
                "prediction_message": (
                    prediction.get(
                        "message",
                        "",
                    )
                ),
                "prediction_error": (
                    prediction.get(
                        "error",
                        "",
                    )
                ),
            }
        )

        sys.exit(0)

    # ========================================================
    # PREDICTED NAME
    # ========================================================

    predicted_name = str(
        prediction.get(
            "predicted_name",
            "",
        )
    ).strip()

    confidence = prediction.get(
        "confidence",
        0,
    )

    # ========================================================
    # EMPTY PREDICTION
    # ========================================================

    if not predicted_name:

        print_json(
            {
                "success": False,
                "message": ("Unable to recognize you. " "Please try again."),
                "employee_id": employee_id,
                "registered_name": (registered_name),
                "predicted_name": "",
                "confidence": confidence,
            }
        )

        sys.exit(0)

    # ========================================================
    # COMPARE NAMES
    # ========================================================

    names_match = registered_name.casefold() == predicted_name.casefold()

    debug(f"Predicted name : " f"{predicted_name}")

    debug(f"Confidence     : " f"{confidence}%")

    debug(f"Names match    : " f"{names_match}")

    # ========================================================
    # NOT MATCHED
    # ========================================================

    if not names_match:

        print_json(
            {
                "success": False,
                "message": ("Unable to recognize you. " "Please try again."),
                "employee_id": employee_id,
                "registered_name": (registered_name),
                "predicted_name": (predicted_name),
                "confidence": confidence,
                "image": str(CURRENT_IMAGE_FILE),
            }
        )

        sys.exit(0)

    # ========================================================
    # CHECK DUPLICATE
    # ========================================================

    if already_attended_today(employee_id):

        current_time = datetime.now().strftime("%H:%M:%S")

        print_json(
            {
                "success": True,
                "already_attended": True,
                "message": (
                    f"Hi {registered_name}, "
                    "your attendance is already "
                    "recorded for today."
                ),
                "employee_id": employee_id,
                "name": registered_name,
                "predicted_name": (predicted_name),
                "confidence": confidence,
                "date": (datetime.now().strftime("%d-%m-%Y")),
                "time": current_time,
                "image": str(CURRENT_IMAGE_FILE),
            }
        )

        sys.exit(0)

    # ========================================================
    # SAVE ATTENDANCE
    # ========================================================

    try:

        save_attendance(employee_id)

    except Exception as error:

        debug("Attendance save error:")

        debug(str(error))

        print_json(
            {
                "success": False,
                "message": ("Attendance could " "not be saved."),
                "error": str(error),
                "attendance_file": str(ATTENDANCE_FILE),
            }
        )

        sys.exit(0)

    # ========================================================
    # SUCCESS
    # ========================================================

    print_json(
        {
            "success": True,
            "already_attended": False,
            "message": (
                f"Hi {registered_name}, " "attendance recorded " "successfully."
            ),
            "employee_id": employee_id,
            "name": registered_name,
            "predicted_name": (predicted_name),
            "confidence": confidence,
            "date": (datetime.now().strftime("%d-%m-%Y")),
            "time": (datetime.now().strftime("%H:%M:%S")),
            "image": str(CURRENT_IMAGE_FILE),
            "attendance_file": str(ATTENDANCE_FILE),
        }
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
