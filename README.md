# Speech Emotion Classification - Group 02 (G2)

Welcome to the **Group 02 (G2)** machine learning project repository for **Speech Emotion Classification** using the RAVDESS Speech Audio Dataset.

---

## 📌 Project Overview

- **Project:** Speech Emotion Classification using RAVDESS
- **Client / Domain:** CallConnect Speech / Customer Support
- **Dataset:** RAVDESS (Ryerson Audio-Visual Database of Emotional Speech and Song)
- **Primary Metrics:** Classification Accuracy & Confusion Matrix (Macro-F1)
- **Current Stage:** **Data Analysis (DA) Stage Completed**
- **Team Roles:** Kenisha (Data Engineer), Data Analyst (DA Stage Completed)

---

## 📂 Project Repository Structure

```text
Group-2-Speech-Recognition-Emotion-Classification/
│
├── data/
│   ├── raw/
│   │   └── RAVDESS/
│   │       ├── Actor_01/
│   │       ├── Actor_02/
│   │       ├── ...
│   │       └── Actor_24/
│   │
│   └── processed/
│       ├── dataset_metadata.csv
│       ├── train_metadata.csv
│       ├── test_metadata.csv
│       ├── train_features.csv
│       └── test_features.csv
│
├── report/
│   ├── audio_quality.csv
│   ├── corrupted_files.csv
│   ├── data_quality_audit.csv
│   ├── dataset_documentation.docx
│   ├── data_analysis_report.pdf
│   └── figures/
│       ├── fig01_emotion_distribution.png
│       ├── fig02_emotion_percentage_donut.png
│       ├── fig03_actor_distribution.png
│       ├── fig04_duration_histogram.png
│       ├── fig05_duration_boxplot.png
│       ├── fig06_duration_by_emotion.png
│       ├── fig07_sample_rate_distribution.png
│       ├── fig08_channel_distribution.png
│       ├── fig09_actor_emotion_heatmap.png
│       ├── fig10_duration_by_intensity.png
│       └── fig11_train_test_split_gender.png
│
├── src/
│   └── data_pipeline.py
│
├── notebooks/
│   ├── 01_Data_Engineering.ipynb
│   └── 02_Data_Analysis.ipynb
│
├── presentation/
│   └── Client_Pitch.pptx
│
├── README.md
├── requirements.txt
└── .gitignore
```

> **Note:** Downstream components (`models/`, `dashboard/`, `src/model.py`, `src/preprocessing.py`, `src/predict.py`, etc.) will be added in subsequent stages by their respective team members (Data Scientist, ML Engineer, Analytics Engineer, and BI Developer).

---

## 🛠️ Data Engineering Pipeline & Responsibilities

The **Data Engineering** stage establishes a reproducible, validated, and leakage-safe data foundation:

1. **Raw Dataset Ingestion**: Organizes original RAVDESS audio across 24 actor directories (`Actor_01` to `Actor_24`) without modifying raw `.wav` files.
2. **Metadata Extraction**: Parses RAVDESS filename conventions to extract `actor_id`, `gender`, `modality`, `vocal_channel`, `emotion_code`, `emotion`, `intensity`, `statement`, and `repetition`.
3. **Data Quality & Schema Validation**: Performs missing value checks, duplicate detection, and schema compliance.
4. **Corrupted Audio & Quality Check**: Verifies audio signal integrity using `librosa` and `soundfile` to extract sampling rate, channel count, duration, and sample length.
5. **Outlier Detection**: Identifies duration anomalies outside normal operational limits (2.0s - 6.0s).
6. **Leakage-Safe Train/Test Splitting**: Implements actor-grouped splitting (`GroupShuffleSplit`) to guarantee zero actor overlap between training (`19 actors`, 1,140 samples) and testing (`5 actors`, 300 samples) sets.
7. **Audit & Report Generation**: Exports complete quality audit logs (`data_quality_audit.csv`, `audio_quality.csv`, `corrupted_files.csv`).

---

## 🚀 Reproducing the Data Engineering Pipeline

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows)
.venv\Scripts\activate

# Activate virtual environment (Linux/macOS)
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Data Pipeline

Execute the end-to-end Data Engineering pipeline script:

```bash
python src/data_pipeline.py
```

### 4. Interactive Notebook

To view and interact with the Data Engineering walkthrough:

```bash
jupyter notebook notebooks/01_Data_Engineering.ipynb
```

---

## 📄 License & Attribution

- **Dataset**: RAVDESS dataset created by Steven R. Livingstone & Frank A. Russo (Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License).
- **Group**: Group 2 (G2) - Machine Learning Lab.
