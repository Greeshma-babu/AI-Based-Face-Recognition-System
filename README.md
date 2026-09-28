# FaceMark Attendance

AI-Based Face Recognition Attendance System built with **Python, YOLO, FastAPI, and Streamlit**.

## Introduction

FaceMark Attendance is an AI-powered attendance system that recognizes registered employees from images and records their attendance automatically.

The system uses **YOLO Classification** for employee recognition, **FastAPI** for backend APIs, and **Streamlit** for the user interface.

## Technologies

- Python 3.10
- Streamlit - Frontend
- FastAPI - Backend
- Uvicorn - API Server
- Ultralytics YOLO - AI Model
- PyTorch - Deep Learning
- Pandas - Data Processing
- Plotly - Charts
- CSV - Data Storage

## Architecture

```text
                    Streamlit
                      app.py
                        |
                        v
                     FastAPI
                      api.py
                    /       \
                   /         \
            /register       /record
                |               |
                v               v
             train.py       record.py
                |               |
                v               v
              YOLO          predict.py
                |               |
                v               v
             best.pt       Recognition
                                |
                                v
                         attendance.csv
```

## Project Structure

```text
AI-Based-Face-Recognition-System/
│
├── app.py              # Streamlit user interface
├── api.py              # FastAPI backend
├── train.py            # YOLO model training
├── predict.py          # Employee prediction
├── record.py           # Attendance processing
├── requirements.txt    # Python dependencies
├── README.md           # Project documentation
│
├── datasets/
│   ├── train/          # Training images
│   └── test/           # Testing images
│
├── runs/
│   └── .../weights/
│       └── best.pt     # Trained YOLO model
│
└── output/
    ├── employees.csv   # Registered employees
    ├── attendance.csv  # Attendance records
    └── training.log    # Training logs
```

## How It Works

### 1. Employee Registration

The user registers an employee by entering the Employee ID and name and uploading at least 15 images.

```text
15 Images
    |
    +-- 10 Images --> Training
    |
    +-- 5 Images --> Testing
```

The images are stored in the `datasets` directory.

### 2. Model Training

`train.py` uses the employee images to train a YOLO classification model.

```text
datasets
    |
    v
train.py
    |
    v
YOLO Training
    |
    v
best.pt
```

Training runs in the background so that the registration API does not wait for the complete training process.

### 3. Attendance Recognition

The user enters an Employee ID and uploads an image.

```text
Employee ID
     |
     v
employees.csv
     |
     v
Registered Name
     |
     v
predict.py
     |
     v
YOLO Model
     |
     v
Predicted Name
     |
     v
Compare Names
     |
   +---+---+
   |       |
 Match   No Match
   |       |
   v       v
Record   Reject
Attendance
```

Attendance is recorded only when the registered employee name matches the predicted employee name.

### 4. Dashboard

The Streamlit dashboard reads data from:

- `output/employees.csv`
- `output/attendance.csv`

## Installation

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd AI-Based-Face-Recognition-System
```

### 2. Create and activate a virtual environment

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Running the Application

Run the backend and the frontend in **two separate terminals** (activate the virtual environment in both).

**Terminal 1 - Start the FastAPI backend**

```bash
uvicorn api:app --reload
```

**Terminal 2 - Start the Streamlit app**

```bash
streamlit run app.py
```

Once both are running:

- Streamlit UI: http://localhost:8501
- FastAPI docs: http://127.0.0.1:8000/docs

## API Endpoints

| Method | Endpoint    | Description                                        |
|--------|-------------|----------------------------------------------------|
| POST   | `/register` | Register an employee and start model training      |
| POST   | `/record`   | Recognize an employee and record attendance        |

## Usage

1. **Register** an employee with an Employee ID, name, and at least 15 images.
2. Wait for the model training to finish in the background.
3. **Record attendance** by entering the Employee ID and uploading a photo.
4. View attendance records and charts on the **Dashboard**.

## Screenshot 
<img width="1867" height="796" alt="image" src="https://github.com/user-attachments/assets/84af577a-c6ae-4724-b65a-04f063f9c837" />
<img width="1897" height="856" alt="image" src="https://github.com/user-attachments/assets/ee4c653d-8473-4fab-9886-b9887dec574a" />
<img width="1912" height="692" alt="image" src="https://github.com/user-attachments/assets/e2e6ef5c-2d99-4a23-8ccc-a09a249c85b6" />
<img width="1907" height="772" alt="image" src="https://github.com/user-attachments/assets/17f7d069-a3fb-4d84-8fae-fe8dbdf7dfc4" />
<img width="1907" height="852" alt="image" src="https://github.com/user-attachments/assets/476e2817-c357-4fbc-b186-f8dc31868b91" />
<img width="1895" height="810" alt="image" src="https://github.com/user-attachments/assets/901aa9ad-baa8-4dd7-83d6-4478db998aad" />



## Author
Greeshma Babu
