import hashlib
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


# ============================================================
# SESSION STATE
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if "employees" not in st.session_state:
    st.session_state.employees = []

if "attendance" not in st.session_state:
    st.session_state.attendance = {
        "Mon": 39,
        "Tue": 41,
        "Wed": 37,
        "Thu": 38,
        "Fri": 40,
        "Sat": 22,
        "Sun": 14,
    }

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
# SIDEBAR
# ============================================================

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
        len(st.session_state.employees),
    )
    st.metric(
        "Marked present today",
        st.session_state.present_today,
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

    page_header(
        "Dashboard",
        "Attendance overview for the current week.",
    )

    m1, m2, m3 = st.columns(3)

    with m1:
        with st.container(border=True):
            st.markdown("**Average attendance**")
            st.markdown(
                '<div class="metric-value">91%</div>',
                unsafe_allow_html=True,
            )
            st.caption("▲ 3% vs last week")

    with m2:
        with st.container(border=True):
            st.markdown("**No. of employees**")
            st.markdown(
                f'<div class="metric-value-light">'
                f"{len(st.session_state.employees)}</div>",
                unsafe_allow_html=True,
            )
            st.caption("Registered employees")

    with m3:
        not_checked = max(
            0,
            len(st.session_state.employees) - st.session_state.present_today,
        )

        with st.container(border=True):
            st.markdown("**Present today**")
            st.markdown(
                f'<div class="metric-value-light">'
                f"{st.session_state.present_today}</div>",
                unsafe_allow_html=True,
            )
            st.caption(f"{not_checked} not yet checked in")

    st.write("")

    with st.container(border=True):
        st.markdown("**Overall attendance — this week**")
        st.caption("All employees, Monday to Sunday")

        days = list(st.session_state.attendance.keys())
        values = list(st.session_state.attendance.values())

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=days,
                y=values,
                text=values,
                textposition="outside",
                marker_color="#f5a623",
                width=0.62,
                hovertemplate="%{x}: %{y}<extra></extra>",
            )
        )

        fig.update_layout(
            height=330,
            margin=dict(l=25, r=25, t=20, b=25),
            paper_bgcolor="#19232f",
            plot_bgcolor="#19232f",
            font=dict(color="#91a0b5", size=10),
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                linecolor="#293746",
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                visible=False,
                range=[0, max(values) + 8],
            ),
            showlegend=False,
        )

        st.plotly_chart(
            fig,
            width="stretch",
            config={"displayModeBar": False},
        )


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
