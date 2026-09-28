import hashlib
import csv
from datetime import date, datetime

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="FaceMark Attendance",
    page_icon="✓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONFIGURATION
# ============================================================

FASTAPI_URL = "http://127.0.0.1:8000"

BASE_DIR = r"C:\AI\FaceAttendence\AI-Based-Face-Recognition-System"

EMPLOYEES_FILE = BASE_DIR + r"\output\employees.csv"

ATTENDANCE_FILE = BASE_DIR + r"\output\attendance.csv"


# ============================================================
# SESSION STATE
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if "employees" not in st.session_state:
    st.session_state.employees = []

if "attendance" not in st.session_state:
    st.session_state.attendance = {}

if "present_today" not in st.session_state:
    st.session_state.present_today = 0

if "logs" not in st.session_state:
    st.session_state.logs = []

if "registered_name" not in st.session_state:
    st.session_state.registered_name = ""

if "registered_id" not in st.session_state:
    st.session_state.registered_id = ""

if "record_result" not in st.session_state:
    st.session_state.record_result = None


# ============================================================
# CSS
# IMPORTANT:
# CSS is used only for styling. Page content does NOT use
# HTML blocks, so Streamlit cannot display raw <div> tags.
# ============================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap'); 
 
    html, body, [class*="css"] { 
        font-family: 'Inter', sans-serif; 
    } 
 
    .stApp { 
        background: #0d1218; 
        color: #f4f7fb; 
    } 
 
    [data-testid="stHeader"] { 
        background: #0d1218; 
    } 
 
    [data-testid="stSidebar"] { 
        background: #18212c; 
        border-right: 1px solid #273342; 
    } 
 
    [data-testid="stSidebar"] > div:first-child { 
        padding-top: 1rem; 
    } 
 
    /* Sidebar buttons */ 
    [data-testid="stSidebar"] div.stButton > button { 
        width: 100%; 
        text-align: left; 
        border: 0; 
        border-radius: 7px; 
        background: transparent; 
        color: #9cabc0; 
        padding: 10px 12px; 
        margin: 2px 0; 
        font-size: 13px; 
    } 
 
    [data-testid="stSidebar"] div.stButton > button:hover { 
        background: #27313d; 
        color: #ffffff; 
    } 
 
    [data-testid="stSidebar"] div.stButton > button[kind="primary"] { 
        background: #3b3832 !important; 
        color: #f5a623 !important; 
    } 
 
    /* Main headings */ 
    .main-title { 
        font-size: 29px; 
        font-weight: 700; 
        color: #f7f9fc; 
        margin-bottom: 3px; 
    } 
 
    .subtitle { 
        color: #91a0b5; 
        font-size: 13px; 
        margin-bottom: 8px; 
    } 
 
    .time-label { 
        color: #7890ac; 
        font-size: 11px; 
        text-align: right; 
        padding-top: 10px; 
    } 
 
    /* Metric cards */ 
    .metric-card { 
        background: #19232f; 
        border: 1px solid #2d3a49; 
        border-radius: 8px; 
        padding: 16px; 
        min-height: 105px; 
    } 
 
    .metric-label { 
        color: #91a0b5; 
        font-size: 11px; 
    } 
 
    .metric-value { 
        color: #f5a623; 
        font-size: 22px; 
        font-weight: 700; 
        margin-top: 5px; 
    } 
 
    .metric-value-light { 
        color: #f2f5f9; 
        font-size: 22px; 
        font-weight: 700; 
        margin-top: 5px; 
    } 
 
    .metric-note { 
        color: #65e69a; 
        font-size: 10px; 
        margin-top: 4px; 
    } 
 
    .metric-note-muted { 
        color: #8c9caf; 
        font-size: 10px; 
        margin-top: 4px; 
    } 
 
    /* Native Streamlit containers */ 
    div[data-testid="stVerticalBlockBorderWrapper"] { 
        background: #19232f; 
        border-color: #2d3a49; 
        border-radius: 8px; 
    } 
 
    /* Inputs */ 
    div[data-baseweb="input"] > div, 
    div[data-baseweb="textarea"] > div { 
        background: #202b38; 
        border-color: #3b4b5f; 
    } 
 
    div[data-baseweb="input"] input, 
    div[data-baseweb="textarea"] textarea { 
        color: #f4f7fb; 
    } 
 
    div[data-testid="stFileUploader"] { 
        background: #202b38; 
        border: 1px dashed #3b4b5f; 
        border-radius: 8px; 
    } 
 
    div[data-testid="stFileUploader"] section { 
        padding: 10px; 
    } 
 
    div[data-testid="stFileUploader"] label { 
        color: #a7b4c5; 
    } 
 
    div[data-testid="stCameraInput"] { 
        background: #202b38; 
        border: 1px solid #2d3a49; 
        border-radius: 8px; 
    } 
 
    /* Primary buttons */ 
    button[kind="primary"] { 
        background: #f5a623 !important; 
        color: #111820 !important; 
        border: none !important; 
        font-weight: 600 !important; 
    } 
 
    button[kind="primary"]:hover { 
        background: #ffc15a !important; 
    } 
 
    /* Progress */ 
    div[data-testid="stProgress"] > div > div > div { 
        background: #f5a623; 
    } 
 
    /* Dataframe */ 
    [data-testid="stDataFrame"] { 
        border: 1px solid #2d3a49; 
        border-radius: 8px; 
    } 
 
    hr { 
        border-color: #2d3a49; 
    } 
 
    .footer-text { 
        text-align: center; 
        color: #5f7187; 
        font-size: 10px; 
        margin-top: 35px; 
        padding-bottom: 15px; 
    } 
    </style> 
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================


def go_to(page_name):
    st.session_state.page = page_name
    st.session_state.record_result = None
    st.rerun()


def now_text():
    return datetime.now().strftime("%a, %d %b · %H:%M")


def image_hash(uploaded_file):
    if uploaded_file is None:
        return None
    return hashlib.sha256(uploaded_file.getvalue()).hexdigest()


def reset_record():
    st.session_state.record_result = None
    st.rerun()


def get_error_message(response):
    try:
        data = response.json()
        if isinstance(data, dict):
            return data.get("detail", data.get("message", "Request failed."))
    except Exception:
        pass
    return response.text or "Request failed."


# ============================================================
# DASHBOARD DATA HELPERS
# ============================================================


def read_employees_from_csv():
    """
    Read registered employees directly from output/employees.csv.
    Supports:
        employee_id,name
        EMP-ID,Name
        Employee ID,Name
    """

    employees = []

    try:
        df = pd.read_csv(
            EMPLOYEES_FILE,
            encoding="utf-8-sig",
        )

    except UnicodeDecodeError:
        try:
            df = pd.read_csv(
                EMPLOYEES_FILE,
                encoding="utf-16",
            )
        except Exception:
            return employees

    except Exception:
        return employees

    if df.empty:
        return employees

    # Normalize column names
    normalized_columns = {
        str(column)
        .strip()
        .lower()
        .replace("-", "")
        .replace("_", "")
        .replace(" ", ""): column
        for column in df.columns
    }

    employee_id_column = None
    name_column = None

    for normalized, original in normalized_columns.items():

        if normalized in {
            "employeeid",
            "empid",
            "id",
            "employee",
        }:
            employee_id_column = original

        if normalized in {
            "name",
            "employeename",
        }:
            name_column = original

    # Fallback to first two columns
    if employee_id_column is None and len(df.columns) >= 1:
        employee_id_column = df.columns[0]

    if name_column is None and len(df.columns) >= 2:
        name_column = df.columns[1]

    if employee_id_column is None:
        return employees

    for _, row in df.iterrows():

        employee_id = str(row.get(employee_id_column, "")).strip()

        if not employee_id:
            continue

        name = ""

        if name_column is not None:
            name = str(row.get(name_column, "")).strip()

        if name.lower() == "nan":
            name = ""

        employees.append(
            {
                "id": employee_id,
                "name": name,
            }
        )

    return employees


def read_attendance_csv():
    """
    Read attendance.csv directly.

    Expected structure:

    Date (DD-MM-YYYY),Total Attendance,EMP-1001,EMP-1002,...

    Returns the complete DataFrame.
    """

    try:

        df = pd.read_csv(
            ATTENDANCE_FILE,
            encoding="utf-8-sig",
        )

    except UnicodeDecodeError:

        try:
            df = pd.read_csv(
                ATTENDANCE_FILE,
                encoding="utf-16",
            )
        except Exception:
            return pd.DataFrame()

    except Exception:
        return pd.DataFrame()

    if df.empty:
        return pd.DataFrame()

    # Remove completely empty rows
    df = df.dropna(how="all").reset_index(drop=True)

    return df


def find_column(df, possible_names):
    """
    Find a column using normalized names.
    """

    normalized_targets = {
        str(name).strip().lower().replace("-", "").replace("_", "").replace(" ", "")
        for name in possible_names
    }

    for column in df.columns:

        normalized = (
            str(column)
            .strip()
            .lower()
            .replace("-", "")
            .replace("_", "")
            .replace(" ", "")
        )

        if normalized in normalized_targets:
            return column

    return None


def get_today_attendance():
    """
    Get today's attendance information from attendance.csv.

    Returns:
        total_attendance
        present_employee_ids
        today_row
    """

    df = read_attendance_csv()

    if df.empty:
        return 0, set(), None

    date_column = find_column(
        df,
        [
            "Date (DD-MM-YYYY)",
            "Date",
            "Attendance Date",
        ],
    )

    total_column = find_column(
        df,
        [
            "Total Attendance",
            "TotalAttendance",
            "Total",
        ],
    )

    if date_column is None:
        return 0, set(), None

    today_string = date.today().strftime("%d-%m-%Y")

    today_row = None

    for _, row in df.iterrows():

        row_date = str(row.get(date_column, "")).strip()

        if row_date == today_string:
            today_row = row
            break

    if today_row is None:
        return 0, set(), None

    # --------------------------------------------------------
    # Total Attendance
    # --------------------------------------------------------

    total_attendance = 0

    if total_column is not None:

        try:
            value = today_row.get(
                total_column,
                0,
            )

            if pd.notna(value):
                total_attendance = int(float(value))

        except (
            TypeError,
            ValueError,
        ):
            total_attendance = 0

    # --------------------------------------------------------
    # Employee IDs marked present today
    # --------------------------------------------------------

    present_employee_ids = set()

    employees = read_employees_from_csv()

    employee_ids = {employee["id"] for employee in employees}

    for employee_id in employee_ids:

        if employee_id not in df.columns:
            continue

        try:

            value = today_row.get(
                employee_id,
                0,
            )

            if pd.notna(value):

                numeric_value = float(value)

                if numeric_value >= 1:
                    present_employee_ids.add(employee_id)

        except (
            TypeError,
            ValueError,
        ):
            continue

    # --------------------------------------------------------
    # Fallback:
    # If employee columns were not found, use Total Attendance
    # --------------------------------------------------------

    if not present_employee_ids and total_attendance > 0:

        employee_columns_found = any(
            employee_id in df.columns for employee_id in employee_ids
        )

        if not employee_columns_found:
            return (
                total_attendance,
                set(),
                today_row,
            )

    return (
        total_attendance,
        present_employee_ids,
        today_row,
    )


def get_dashboard_data():
    """
    Get all Dashboard values directly from CSV files.
    """

    employees = read_employees_from_csv()

    total_registered = len(employees)

    total_attendance, present_employee_ids, today_row = get_today_attendance()

    # --------------------------------------------------------
    # If employee columns are available, use their values to
    # calculate today's present count.
    #
    # Otherwise use Total Attendance.
    # --------------------------------------------------------

    if today_row is not None:

        employee_column_count = 0

        for employee in employees:

            employee_id = employee["id"]

            if employee_id in today_row.index:
                employee_column_count += 1

        if employee_column_count > 0:

            present_today = len(present_employee_ids)

        else:

            present_today = total_attendance

    else:

        present_today = 0

    # --------------------------------------------------------
    # Total attendance value
    #
    # This is taken directly from today's
    # "Total Attendance" column.
    # --------------------------------------------------------

    total_attendance_value = total_attendance

    # --------------------------------------------------------
    # Employee chart data
    # --------------------------------------------------------

    employee_chart = []

    for employee in employees:

        employee_id = employee["id"]

        value = 0

        if today_row is not None:

            try:

                if employee_id in today_row.index:

                    raw_value = today_row.get(
                        employee_id,
                        0,
                    )

                    if pd.notna(raw_value):
                        value = int(float(raw_value))

            except (
                TypeError,
                ValueError,
            ):
                value = 0

        employee_chart.append(
            {
                "employee_id": employee_id,
                "attendance": value,
            }
        )

    not_checked = max(
        0,
        total_registered - present_today,
    )

    return {
        "employees": employees,
        "registered_count": total_registered,
        "total_attendance": total_attendance_value,
        "present_today": present_today,
        "not_checked": not_checked,
        "employee_chart": employee_chart,
    }


# ============================================================
# SIDEBAR
# ============================================================

dashboard_data = get_dashboard_data()

with st.sidebar:
    # Logo
    logo_col1, logo_col2 = st.columns([1, 4])

    with logo_col1:
        st.markdown(
            "<div style='background:#f5a623;color:#151a20;"
            "width:38px;height:38px;border-radius:9px;"
            "display:flex;align-items:center;justify-content:center;"
            "font-weight:700;font-size:18px;'>✓</div>",
            unsafe_allow_html=True,
        )

    with logo_col2:
        st.markdown("**FaceMark**  \n" "**Attendance**")

    st.write("")

    pages = ["Dashboard", "Register", "Record", "Log"]

    for page_name in pages:
        if st.session_state.page == page_name:
            if st.button(
                f"●  {page_name}",
                key=f"nav_{page_name}",
                type="primary",
                width="stretch",
            ):
                go_to(page_name)
        else:
            if st.button(
                f"•  {page_name}",
                key=f"nav_{page_name}",
                width="stretch",
            ):
                go_to(page_name)

    st.divider()

    st.caption("SYSTEM SUMMARY")

    st.metric(
        "People registered",
        dashboard_data["registered_count"],
    )

    st.metric(
        "Marked present today",
        dashboard_data["present_today"],
    )


# ============================================================
# COMMON PAGE HEADER
# ============================================================


def page_header(title, subtitle):
    left, right = st.columns([7, 2])

    with left:
        st.markdown(
            f'<div class="main-title">{title}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="subtitle">{subtitle}</div>',
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            f'<div class="time-label">{now_text()}</div>',
            unsafe_allow_html=True,
        )

    st.write("")


# ============================================================
# DASHBOARD
# ============================================================

if st.session_state.page == "Dashboard":

    # Refresh Dashboard data directly from CSV
    dashboard_data = get_dashboard_data()

    page_header(
        "Dashboard",
        "Attendance overview for the current week.",
    )

    m1, m2, m3 = st.columns(3)

    # --------------------------------------------------------
    # TOTAL ATTENDANCE
    # From attendance.csv -> today's Total Attendance
    # --------------------------------------------------------

    with m1:
        with st.container(border=True):

            st.markdown("**Total attendance**")

            st.markdown(
                f'<div class="metric-value">'
                f'{dashboard_data["total_attendance"]}'
                f"</div>",
                unsafe_allow_html=True,
            )

            st.caption("From attendance.csv")

    # --------------------------------------------------------
    # REGISTERED EMPLOYEES
    # From employees.csv
    # --------------------------------------------------------

    with m2:
        with st.container(border=True):

            st.markdown("**No. of employees**")

            st.markdown(
                f'<div class="metric-value-light">'
                f'{dashboard_data["registered_count"]}'
                f"</div>",
                unsafe_allow_html=True,
            )

            st.caption("Registered employees")

    # --------------------------------------------------------
    # PRESENT TODAY
    # From attendance.csv
    # --------------------------------------------------------

    with m3:

        with st.container(border=True):

            st.markdown("**Present today**")

            st.markdown(
                f'<div class="metric-value-light">'
                f'{dashboard_data["present_today"]}'
                f"</div>",
                unsafe_allow_html=True,
            )

            st.caption(f'{dashboard_data["not_checked"]} not yet checked in')

    st.write("")

    # ========================================================
    # EMPLOYEE ATTENDANCE BAR CHART
    # ========================================================

    with st.container(border=True):

        st.markdown("**Employee attendance — today**")

        st.caption("Attendance status based on Employee ID from attendance.csv")

        employee_chart = dashboard_data["employee_chart"]

        if employee_chart:

            chart_df = pd.DataFrame(employee_chart)

            fig = go.Figure()

            fig.add_trace(
                go.Bar(
                    x=chart_df["employee_id"],
                    y=chart_df["attendance"],
                    text=chart_df["attendance"],
                    textposition="outside",
                    marker_color="#f5a623",
                    width=0.62,
                    hovertemplate=(
                        "Employee ID: %{x}" "<br>Attendance: %{y}" "<extra></extra>"
                    ),
                )
            )

            max_value = max(
                1,
                int(chart_df["attendance"].max()),
            )

            fig.update_layout(
                height=330,
                margin=dict(
                    l=25,
                    r=25,
                    t=20,
                    b=25,
                ),
                paper_bgcolor="#19232f",
                plot_bgcolor="#19232f",
                font=dict(
                    color="#91a0b5",
                    size=10,
                ),
                xaxis=dict(
                    showgrid=False,
                    zeroline=False,
                    linecolor="#293746",
                    title="Employee ID",
                ),
                yaxis=dict(
                    showgrid=False,
                    zeroline=False,
                    visible=False,
                    range=[
                        0,
                        max_value + 1,
                    ],
                ),
                showlegend=False,
            )

            st.plotly_chart(
                fig,
                width="stretch",
                config={"displayModeBar": False},
            )

        else:

            st.info("No registered employees found in employees.csv.")


# ============================================================
# REGISTER
# ============================================================

elif st.session_state.page == "Register":

    page_header(
        "Register your face",
        "Upload a minimum of 15 clear photos of your face from "
        "slightly different angles. 10 images will be randomly "
        "selected for training and 5 images for testing.",
    )

    with st.container(border=True):
        left, right = st.columns(2)

        with left:
            name = st.text_input(
                "Full name",
                value=st.session_state.registered_name,
                placeholder="Name",
                key="registration_name",
            )
            st.session_state.registered_name = name

        with right:
            employee_id = st.text_input(
                "Employee ID",
                value=st.session_state.registered_id,
                placeholder="EMP-XXXX",
                key="registration_employee_id",
            )
            st.session_state.registered_id = employee_id

        st.markdown("**Face photos**")
        st.caption("200MB per file • JPG, PNG")

        uploaded = st.file_uploader(
            "Upload face photos",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="registration_images",
        )

        photo_count = len(uploaded) if uploaded else 0

        st.write(f"**{photo_count} / 15 images**")

        if uploaded:
            preview_cols = st.columns(5)

            for i, image_file in enumerate(uploaded[:15]):
                with preview_cols[i % 5]:
                    st.image(
                        image_file,
                        width="stretch",
                    )

            if photo_count > 15:
                st.info(
                    f"{photo_count} images selected. "
                    "The backend can receive all selected images; "
                    "the preview shows the first 15."
                )

        st.progress(min(photo_count / 15, 1.0))

        if photo_count < 15:
            st.warning(f"Please upload {15 - photo_count} more image(s).")
        else:
            st.success("✓ Minimum requirement satisfied.")

        st.info(
            "For best results: good lighting, no sunglasses or masks, "
            "and a mix of straight-on and slight side angles."
        )

        complete = st.button(
            "Complete registration",
            type="primary",
            width="stretch",
        )

    if complete:
        clean_name = name.strip()
        clean_id = employee_id.strip()

        if not clean_name:
            st.error("Please enter the full name.")

        elif not clean_id:
            st.error("Please enter the employee ID.")

        elif photo_count < 15:
            st.warning(
                f"Please upload at least 15 images. "
                f"Currently uploaded: {photo_count}."
            )

        else:
            with st.spinner("Registering face and creating dataset..."):
                try:
                    files = []

                    for image in uploaded:
                        files.append(
                            (
                                "images",
                                (
                                    image.name,
                                    image.getvalue(),
                                    image.type or "image/jpeg",
                                ),
                            )
                        )

                    data = {
                        "name": clean_name,
                        "employee_id": clean_id,
                    }

                    response = requests.post(
                        f"{FASTAPI_URL}/register",
                        data=data,
                        files=files,
                        timeout=120,
                    )

                    if response.status_code == 200:
                        result = response.json()

                        existing = any(
                            employee.get("id") == clean_id
                            for employee in st.session_state.employees
                        )

                        if not existing:
                            st.session_state.employees.append(
                                {
                                    "name": clean_name,
                                    "id": clean_id,
                                    "photos": [image_hash(f) for f in uploaded],
                                }
                            )

                        message = result.get(
                            "message",
                            "Registration completed.",
                        )

                        train_images = result.get(
                            "train_images",
                            10,
                        )

                        test_images = result.get(
                            "test_images",
                            5,
                        )

                        training_started = result.get(
                            "training_started",
                            False,
                        )

                        st.success(f"✓ {message}")

                        with st.container(border=True):
                            st.markdown("### Dataset Created")
                            st.write(f"**Name:** {clean_name}")
                            st.write(f"**Employee ID:** {clean_id}")
                            st.success(f"✓ Training images: {train_images}")
                            st.success(f"✓ Testing images: {test_images}")
                            st.success(
                                "✓ Background training: "
                                + ("Started" if training_started else "Not started")
                            )

                    else:
                        st.error(f"❌ {get_error_message(response)}")

                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to FastAPI.")
                    st.info("Start FastAPI using:\n\n" "`uvicorn api:app --reload`")

                except requests.exceptions.Timeout:
                    st.error("❌ FastAPI request timed out.")

                except Exception as exc:
                    st.error(f"❌ Registration error: {exc}")


# ============================================================
# RECORD ATTENDANCE
# ============================================================

elif st.session_state.page == "Record":

    page_header(
        "Record attendance",
        "Enter your Employee ID and provide a face image " "to record attendance.",
    )

    result = st.session_state.record_result

    if result is not None:

        if result.get("success"):

            message = result.get(
                "message",
                "Attendance recorded successfully.",
            )

            confidence = result.get("confidence")

            st.success("✓ Attendance Recorded")
            st.info(f"{message}\n\n" f"Employee ID: {result.get('employee_id', '')}")

            if confidence is not None:
                try:
                    st.metric(
                        "Confidence",
                        f"{float(confidence):.2f}%",
                    )
                except (TypeError, ValueError):
                    st.metric(
                        "Confidence",
                        str(confidence),
                    )

        else:

            message = result.get(
                "message",
                "Sorry, we couldn't recognize you. Please try again.",
            )

            st.error("Recognition Failed")
            st.warning(message)

        if st.button(
            "Another Record",
            type="primary",
            width="stretch",
        ):
            reset_record()

    else:

        employee_id = st.text_input(
            "Employee ID",
            placeholder="EMP-1001",
            key="attendance_employee_id",
        )

        st.markdown("**Recognition method**")

        mode = st.radio(
            "Recognition method",
            ["Live camera", "Upload photo"],
            horizontal=True,
            label_visibility="collapsed",
            key="attendance_mode",
        )

        camera_image = None
        uploaded_photo = None

        if mode == "Live camera":

            camera_image = st.camera_input(
                "Look directly at the camera",
                key="attendance_camera",
            )

            if camera_image is not None:
                st.image(
                    camera_image,
                    caption="Camera capture",
                    width="content",
                )
            else:
                st.info("Take a clear face photo using the camera.")

        else:

            uploaded_photo = st.file_uploader(
                "Upload a face photo",
                type=["jpg", "jpeg", "png"],
                key="attendance_upload",
            )

            if uploaded_photo:
                st.image(
                    uploaded_photo,
                    caption="Selected photo",
                    width="content",
                )

        record_button = st.button(
            "Record Attendance",
            type="primary",
            width="stretch",
        )

        if record_button:

            clean_employee_id = employee_id.strip()

            if not clean_employee_id:
                st.error("Please enter your Employee ID.")

            elif camera_image is None and uploaded_photo is None:
                st.warning("Please capture or upload a face photo.")

            else:

                selected_image = (
                    camera_image if camera_image is not None else uploaded_photo
                )

                with st.spinner("Recognizing face and recording attendance..."):

                    try:

                        image_name = getattr(
                            selected_image,
                            "name",
                            "camera.jpg",
                        )

                        image_type = getattr(
                            selected_image,
                            "type",
                            "image/jpeg",
                        )

                        files = {
                            "image": (
                                image_name,
                                selected_image.getvalue(),
                                image_type or "image/jpeg",
                            )
                        }

                        data = {"employee_id": clean_employee_id}

                        response = requests.post(
                            f"{FASTAPI_URL}/record",
                            data=data,
                            files=files,
                            timeout=120,
                        )

                        if response.status_code == 200:
                            result = response.json()
                        else:
                            result = {
                                "success": False,
                                "message": get_error_message(response),
                            }

                        st.session_state.record_result = result

                        if result.get("success"):

                            if not result.get(
                                "already_attended",
                                False,
                            ):
                                st.session_state.present_today += 1

                            # Prevent duplicate log insertion on rerun
                            if not result.get(
                                "already_attended",
                                False,
                            ):
                                st.session_state.logs.insert(
                                    0,
                                    {
                                        "date": result.get(
                                            "date",
                                            date.today().strftime("%d-%m-%Y"),
                                        ),
                                        "time": datetime.now().strftime("%H:%M:%S"),
                                        "name": result.get(
                                            "name",
                                            "",
                                        ),
                                        "employee_id": result.get(
                                            "employee_id",
                                            clean_employee_id,
                                        ),
                                        "status": "Present",
                                    },
                                )

                        st.rerun()

                    except requests.exceptions.ConnectionError:
                        st.error("❌ Cannot connect to FastAPI.")
                        st.info("Start FastAPI using:\n\n" "`uvicorn api:app --reload`")

                    except requests.exceptions.Timeout:
                        st.error("❌ Recognition request timed out.")

                    except Exception as exc:
                        st.error(f"❌ Attendance error: {exc}")


# ============================================================
# LOG
# ============================================================

elif st.session_state.page == "Log":

    page_header(
        "Attendance log",
        "View recorded attendance entries.",
    )

    if st.session_state.logs:
        df = pd.DataFrame(st.session_state.logs)
    else:
        df = pd.DataFrame(
            columns=[
                "date",
                "time",
                "name",
                "employee_id",
                "status",
            ]
        )

    with st.container(border=True):
        st.markdown("**Attendance records**")
        st.caption(f"{len(df)} attendance record(s)")

        st.dataframe(
            df,
            width="stretch",
            hide_index=True,
            column_config={
                "date": "Date",
                "time": "Time",
                "name": "Employee",
                "employee_id": "Employee ID",
                "status": "Status",
            },
        )

    st.write("")

    csv_data = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Export attendance CSV",
        data=csv_data,
        file_name="attendance_log.csv",
        mime="text/csv",
        width="stretch",
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    '<div class="footer-text">'
    "FaceMark Attendance · AI Face Recognition · "
    "Real-Time Attendance"
    "</div>",
    unsafe_allow_html=True,
)
