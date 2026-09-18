import os
import pandas as pd
import librosa


# Resolve project and dataset paths dynamically with fallbacks
_dir = os.path.dirname(os.path.abspath(__file__))
_possible_roots = [
    os.path.abspath(os.path.join(_dir, "..")),
    os.path.abspath(os.path.join(_dir, "..", "data", "RAVDESS")),
    r"C:/Users/kenis/OneDrive/Desktop/RAVDESS",
]
PROJECT_PATH = next(
    (p for p in _possible_roots if os.path.exists(os.path.join(p, "data", "raw", "Audio_Speech_Actors_01-24_16k (1) - Copy"))),
    _possible_roots[0]
)

DATASET_PATH = os.path.join(
    PROJECT_PATH,
    "data",
    "raw",
    "Audio_Speech_Actors_01-24_16k (1) - Copy"
)

REPORTS_PATH = os.path.join(
    PROJECT_PATH,
    "reports"
)


emotion_map = {
    1: "neutral",
    2: "calm",
    3: "happy",
    4: "sad",
    5: "angry",
    6: "fearful",
    7: "disgust",
    8: "surprised"
}


def find_audio_files():

    wav_files = []

    for root, dirs, files in os.walk(DATASET_PATH):

        for file in files:

            if file.lower().endswith(".wav"):
                wav_files.append(
                    os.path.join(root, file)
                )

    return wav_files


def create_metadata(wav_files):

    records = []

    for filepath in wav_files:

        filename = os.path.basename(filepath)

        parts = filename.replace(".wav", "").split("-")

        if len(parts) != 7:
            continue

        try:

            emotion_code = int(parts[2])

            records.append({
                "filename": filename,
                "filepath": filepath,
                "modality": int(parts[0]),
                "vocal_channel": int(parts[1]),
                "emotion_code": emotion_code,
                "emotion": emotion_map.get(emotion_code),
                "intensity": int(parts[3]),
                "statement": int(parts[4]),
                "repetition": int(parts[5]),
                "actor": int(parts[6])
            })

        except ValueError:
            continue

    return pd.DataFrame(records)


def check_audio_quality(df):

    results = []
    errors = []

    for _, row in df.iterrows():

        try:

            y, sr = librosa.load(
                row["filepath"],
                sr=None
            )

            duration = len(y) / sr

            results.append({
                "filename": row["filename"],
                "sampling_rate": sr,
                "duration_seconds": duration,
                "samples": len(y),
                "status": "OK"
            })

        except Exception as e:

            errors.append({
                "filename": row["filename"],
                "error": str(e),
                "status": "ERROR"
            })

    return pd.DataFrame(results), pd.DataFrame(errors)


def run_pipeline():

    print("Starting RAVDESS Data Pipeline...")

    os.makedirs(REPORTS_PATH, exist_ok=True)

    wav_files = find_audio_files()

    print("Audio files found:", len(wav_files))

    df = create_metadata(wav_files)

    print("Metadata records:", len(df))

    metadata_path = os.path.join(
        REPORTS_PATH,
        "dataset_metadata.csv"
    )

    df.to_csv(
        metadata_path,
        index=False
    )

    quality_df, error_df = check_audio_quality(df)

    quality_df.to_csv(
        os.path.join(
            REPORTS_PATH,
            "audio_quality.csv"
        ),
        index=False
    )

    error_df.to_csv(
        os.path.join(
            REPORTS_PATH,
            "corrupted_files.csv"
        ),
        index=False
    )

    print("Readable files:", len(quality_df))
    print("Unreadable files:", len(error_df))

    print("Pipeline completed successfully!")


if __name__ == "__main__":
    run_pipeline()