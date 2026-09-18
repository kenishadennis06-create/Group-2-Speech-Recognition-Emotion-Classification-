import os
import pandas as pd
import numpy as np
import librosa
import soundfile as sf
from sklearn.model_selection import GroupShuffleSplit


# Resolve project root dynamically relative to this script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

RAW_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "RAVDESS")
PROCESSED_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed")
REPORTS_PATH = os.path.join(PROJECT_ROOT, "report")

EMOTION_MAP = {
    1: "neutral",
    2: "calm",
    3: "happy",
    4: "sad",
    5: "angry",
    6: "fearful",
    7: "disgust",
    8: "surprised"
}

EXPECTED_SCHEMA = [
    "filename", "filepath", "actor_id", "actor", "gender",
    "modality", "vocal_channel", "emotion_code", "emotion",
    "intensity", "statement", "repetition"
]


def discover_dataset(raw_path):
    """Discovers audio files and verifies actor folder structure."""
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw dataset path does not exist: {raw_path}")

    actor_dirs = sorted([
        d for d in os.listdir(raw_path)
        if os.path.isdir(os.path.join(raw_path, d)) and d.startswith("Actor_")
    ])

    wav_files = []
    for root, _, files in os.walk(raw_path):
        for f in files:
            if f.lower().endswith(".wav"):
                wav_files.append(os.path.join(root, f))

    return actor_dirs, sorted(wav_files)


def extract_metadata(wav_files):
    """Extracts structured metadata from RAVDESS filename conventions."""
    records = []
    invalid_filenames = []

    for filepath in wav_files:
        filename = os.path.basename(filepath)
        name_part, _ = os.path.splitext(filename)
        parts = name_part.split("-")

        if len(parts) != 7:
            invalid_filenames.append(filename)
            continue

        try:
            modality = int(parts[0])
            vocal_channel = int(parts[1])
            emotion_code = int(parts[2])
            intensity = int(parts[3])
            statement = int(parts[4])
            repetition = int(parts[5])
            actor_id = int(parts[6])

            if emotion_code not in EMOTION_MAP:
                invalid_filenames.append(filename)
                continue

            gender = "female" if actor_id % 2 == 0 else "male"
            actor_str = f"Actor_{actor_id:02d}"

            records.append({
                "filename": filename,
                "filepath": filepath,
                "actor_id": actor_id,
                "actor": actor_str,
                "gender": gender,
                "modality": modality,
                "vocal_channel": vocal_channel,
                "emotion_code": emotion_code,
                "emotion": EMOTION_MAP[emotion_code],
                "intensity": intensity,
                "statement": statement,
                "repetition": repetition
            })
        except ValueError:
            invalid_filenames.append(filename)
            continue

    df = pd.DataFrame(records)
    return df, invalid_filenames


def validate_schema(df):
    """Validates dataframe schema and missing values."""
    missing_cols = [col for col in EXPECTED_SCHEMA if col not in df.columns]
    null_counts = df.isnull().sum().to_dict()
    return missing_cols, null_counts


def check_audio_quality(df):
    """Validates audio readability, sampling rate, duration, and channel counts."""
    quality_records = []
    corrupted_records = []

    for _, row in df.iterrows():
        filepath = row["filepath"]
        filename = row["filename"]

        try:
            # Check soundfile metadata without full decode for channels
            info = sf.info(filepath)
            channels = info.channels

            # Load audio signal via librosa
            y, sr = librosa.load(filepath, sr=None)
            duration = len(y) / sr

            quality_records.append({
                "filename": filename,
                "filepath": filepath,
                "sampling_rate": sr,
                "channels": channels,
                "duration_seconds": round(duration, 4),
                "samples": len(y),
                "status": "OK"
            })
        except Exception as e:
            corrupted_records.append({
                "filename": filename,
                "filepath": filepath,
                "error": str(e),
                "status": "CORRUPTED"
            })

    quality_df = pd.DataFrame(quality_records)
    corrupted_df = pd.DataFrame(corrupted_records)
    return quality_df, corrupted_df


def detect_duration_outliers(quality_df, min_sec=2.0, max_sec=6.0):
    """Detects duration outliers outside specified thresholds."""
    if quality_df.empty:
        return pd.DataFrame()
    outliers = quality_df[
        (quality_df["duration_seconds"] < min_sec) | (quality_df["duration_seconds"] > max_sec)
    ].copy()
    return outliers


def perform_leakage_safe_split(df, test_size=0.20, random_state=42):
    """Splits dataset strictly by actor identity to prevent data leakage."""
    groups = df["actor_id"]
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, test_idx = next(splitter.split(df, df["emotion"], groups=groups))

    train_df = df.iloc[train_idx].copy()
    test_df = df.iloc[test_idx].copy()

    train_actors = set(train_df["actor_id"].unique())
    test_actors = set(test_df["actor_id"].unique())
    overlap = train_actors.intersection(test_actors)

    return train_df, test_df, train_actors, test_actors, overlap


def run_pipeline():
    """Runs the complete end-to-end Data Engineering pipeline."""
    print("=" * 60)
    print("      CallConnect Speech - Data Engineering Pipeline      ")
    print("=" * 60)

    os.makedirs(PROCESSED_DATA_PATH, exist_ok=True)
    os.makedirs(REPORTS_PATH, exist_ok=True)

    # 1. Dataset Discovery
    actor_dirs, wav_files = discover_dataset(RAW_DATA_PATH)
    print(f"[1/8] Dataset Discovery:")
    print(f"      - Raw Path: {RAW_DATA_PATH}")
    print(f"      - Actor Directories Found: {len(actor_dirs)} (Expected: 24)")
    print(f"      - Total WAV Files Discovered: {len(wav_files)}")

    # 2. Metadata Extraction
    df, invalid_filenames = extract_metadata(wav_files)
    print(f"\n[2/8] Metadata Extraction:")
    print(f"      - Valid Records Extracted: {len(df)}")
    print(f"      - Invalid Filenames Encountered: {len(invalid_filenames)}")

    # 3. Schema & Missing Value Check
    missing_cols, null_counts = validate_schema(df)
    dup_filenames = df["filename"].duplicated().sum()
    dup_filepaths = df["filepath"].duplicated().sum()
    print(f"\n[3/8] Schema & Quality Validation:")
    print(f"      - Missing Columns: {missing_cols if missing_cols else 'None'}")
    print(f"      - Duplicate Filenames: {dup_filenames}")
    print(f"      - Duplicate Filepaths: {dup_filepaths}")

    # 4. Audio Quality & Corrupted Check
    print(f"\n[4/8] Audio Quality & Corrupted File Check:")
    quality_df, corrupted_df = check_audio_quality(df)
    print(f"      - Successfully Verified Audio Files: {len(quality_df)}")
    print(f"      - Corrupted Files Detected: {len(corrupted_df)}")

    # Merge quality columns into metadata
    if not quality_df.empty:
        merged_metadata = df.merge(
            quality_df[["filename", "sampling_rate", "channels", "duration_seconds", "samples"]],
            on="filename",
            how="left"
        )
    else:
        merged_metadata = df.copy()

    # 5. Outlier Detection
    outliers_df = detect_duration_outliers(quality_df)
    print(f"\n[5/8] Duration Outlier Check:")
    print(f"      - Files Shorter < 2.0s or Longer > 6.0s: {len(outliers_df)}")

    # 6. Leakage-Safe Train/Test Split
    train_df, test_df, train_actors, test_actors, overlap = perform_leakage_safe_split(merged_metadata)
    print(f"\n[6/8] Leakage-Safe Train/Test Split (by Actor ID):")
    print(f"      - Training Set Size: {len(train_df)} samples ({len(train_actors)} actors)")
    print(f"      - Testing Set Size:  {len(test_df)} samples ({len(test_actors)} actors)")
    print(f"      - Training Actors:   {sorted(list(train_actors))}")
    print(f"      - Testing Actors:    {sorted(list(test_actors))}")
    print(f"      - Actor Overlap (Leakage Check): {overlap} -> Leakage Detected: {len(overlap) > 0}")

    # 7. Save Processed Metadata
    full_metadata_path = os.path.join(PROCESSED_DATA_PATH, "dataset_metadata.csv")
    train_metadata_path = os.path.join(PROCESSED_DATA_PATH, "train_metadata.csv")
    test_metadata_path = os.path.join(PROCESSED_DATA_PATH, "test_metadata.csv")

    merged_metadata.to_csv(full_metadata_path, index=False)
    train_df.to_csv(train_metadata_path, index=False)
    test_df.to_csv(test_metadata_path, index=False)

    print(f"\n[7/8] Processed Data Saved:")
    print(f"      - Full Metadata:  {full_metadata_path}")
    print(f"      - Train Metadata: {train_metadata_path}")
    print(f"      - Test Metadata:  {test_metadata_path}")

    # 8. Save Audit & Quality Reports
    audio_quality_path = os.path.join(REPORTS_PATH, "audio_quality.csv")
    corrupted_files_path = os.path.join(REPORTS_PATH, "corrupted_files.csv")
    audit_report_path = os.path.join(REPORTS_PATH, "data_quality_audit.csv")

    quality_df.to_csv(audio_quality_path, index=False)
    corrupted_df.to_csv(corrupted_files_path, index=False)

    audit_summary = pd.DataFrame([{
        "total_discovered_files": len(wav_files),
        "actor_directories_found": len(actor_dirs),
        "valid_metadata_records": len(df),
        "corrupted_files": len(corrupted_df),
        "duplicate_filenames": dup_filenames,
        "duplicate_filepaths": dup_filepaths,
        "duration_outliers": len(outliers_df),
        "train_samples": len(train_df),
        "test_samples": len(test_df),
        "train_actor_count": len(train_actors),
        "test_actor_count": len(test_actors),
        "actor_overlap_count": len(overlap),
        "leakage_status": "PASSED" if len(overlap) == 0 else "FAILED"
    }])
    audit_summary.to_csv(audit_report_path, index=False)

    print(f"\n[8/8] Audit Reports Generated:")
    print(f"      - Audio Quality:     {audio_quality_path}")
    print(f"      - Corrupted Files:   {corrupted_files_path}")
    print(f"      - Data Quality Audit:{audit_report_path}")

    print("\n" + "=" * 60)
    print("    Data Engineering Pipeline Execution Completed Successfully!   ")
    print("=" * 60)

    return {
        "wav_count": len(wav_files),
        "actor_count": len(actor_dirs),
        "corrupted_count": len(corrupted_df),
        "outliers_count": len(outliers_df),
        "train_count": len(train_df),
        "test_count": len(test_df),
        "actor_overlap": len(overlap)
    }


if __name__ == "__main__":
    run_pipeline()