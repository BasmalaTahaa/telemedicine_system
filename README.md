# 🏥 TeleMedicine IoT Monitoring System

## Project Structure
```
telemedicine_project/
├── telemedicine_system.ipynb   ← Main Jupyter Notebook (submit this)
├── dashboard.py                 ← Streamlit Live Dashboard
└── README.md                    ← This file

Generated after running notebook:
├── telemedicine_data.csv        ← All IoT sensor records
├── telemedicine.db              ← SQLite database
├── telemedicine_log.json        ← JSON event log
├── telemedicine_dashboard.png   ← Analytics chart
└── sensor_distributions.png     ← Sensor histograms
```

## Setup & Run

### 1. Install Dependencies
```bash
pip install numpy pandas matplotlib seaborn jupyter streamlit plotly
```

### 2. Run the Notebook
Open `telemedicine_system.ipynb` in Jupyter and run all cells:
```bash
jupyter notebook telemedicine_system.ipynb
```

### 3. Launch the Dashboard (Optional)
After running the notebook, launch the Streamlit dashboard:
```bash
streamlit run dashboard.py
```

## System Features Checklist

| Requirement | Implementation |
|-------------|---------------|
| 50 patients simultaneously | 50 PatientState objects, 50 producer threads |
| 5 disease groups | CaseType enum (Cardiovascular, Diabetic, Respiratory, Fever, General) |
| ≥3 parameters per patient | 4 sensors per patient |
| IoT-style format | IoTRecord dataclass (patient_id, case_type, sensor_type, timestamp, value) |
| CSV storage | telemedicine_data.csv |
| SQLite storage | telemedicine.db (readings + patient_risk tables) |
| JSON log | telemedicine_log.json |
| Concurrent processing | 50 producer threads + 10 consumer threads (threading) |
| Validation | Missing / Impossible / Out-of-range / Wrong-parameter |
| Risk levels | Normal / Warning / Critical |
| Patient report | Full console output per patient |
| Dashboard | Streamlit with Plotly charts, auto-refresh |

## Clinical Reference Ranges

| Parameter | Normal Low | Normal High | Unit |
|-----------|-----------|-------------|------|
| Heart Rate | 60 | 100 | BPM |
| BP Systolic | 90 | 120 | mmHg |
| BP Diastolic | 60 | 80 | mmHg |
| SpO2 | 95 | 100 | % |
| Glucose | 70 | 140 | mg/dL |
| Insulin | 2 | 25 | µU/mL |
| Respiratory Rate | 12 | 20 | br/min |
| Body Temperature | 36.1 | 37.2 | °C |
