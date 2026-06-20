import pandas as pd
import numpy as np
from pathlib import Path

INPUT_FILE = Path("data/processed/cleaned.csv")
OUTPUT_FILE = Path("data/processed/hotspot_scores.csv")


SEVERITY_MAP = {
    "NO PARKING": 1,
    "WRONG PARKING": 2,
    "DOUBLE PARKING": 2,
    "PARKING OTHER THAN BUS STOP": 2,
    "PARKING OPPOSITE TO ANOTHER PARKED VEHICLE": 2,
    "PARKING NEAR ROAD CROSSING": 3,
    "PARKING NEAR TRAFFIC LIGHT OR ZEBRA CROSS": 3,
    "PARKING NEAR BUSTOP/SCHOOL/HOSPITAL ETC": 3,
    "PARKING ON FOOTPATH": 4,
    "PARKING IN A MAIN ROAD": 5,
    "DEFECTIVE NUMBER PLATE": 1,
    "WITHOUT SIDE MIRROR": 1,
    "USING BLACK FILM/OTHER MATERIALS": 1,
    "CARRYING LENGHTY MATERIAL": 2,
    "OBSTRUCTING DRIVER": 2,
    "DEMANDING EXCESS FARE": 2,
    "REFUSE TO GO FOR HIRE": 2,
    "STOPING ON WHITE/STOP LINE": 3,
    "VIOLATING LANE DISIPLINE": 3,
    "U TURN PROHIBITED": 3,
    "FAIL TO USE SAFETY BELTS": 3,
    "2W/3W - USING MOBILE PHONE": 4,
    "OTHER - USING MOBILE PHONE": 4,
    "RIDER NOT WEARING HELMET": 4,
    "H T V PROHIBITED": 4,
    "AGAINST ONE WAY/NO ENTRY": 5,
    "JUMPING TRAFFIC SIGNAL": 5
}


VEHICLE_MAP = {
    "SCOOTER": 1,
    "MOPED": 1,
    "MOTOR CYCLE": 1,

    "PASSENGER AUTO": 2,
    "MAXI-CAB": 2,

    "CAR": 3,
    "VAN": 3,
    "JEEP": 3,

    "GOODS AUTO": 4,
    "LGV": 4,
    "TEMPO": 4,
    "TANKER": 4,

    "PRIVATE BUS": 5,
    "BUS (BMTC/KSRTC)": 5,
    "TOURIST BUS": 5,
    "SCHOOL VEHICLE": 5,
    "FACTORY BUS": 5,
    "HGV": 5,
    "LORRY/GOODS VEHICLE": 5
}


def get_severity_score(violation_text):
    """
    Handles combined violations like:
    ['PARKING IN A MAIN ROAD','WRONG PARKING']
    """

    violation_text = str(violation_text).upper()

    score = 0

    for key, value in SEVERITY_MAP.items():

        if key in violation_text:
            score = max(score, value)

    return score


def get_vehicle_score(vehicle):
    vehicle = str(vehicle).upper()

    return VEHICLE_MAP.get(vehicle, 2)


def load_data():

    print("Loading cleaned dataset...")

    df = pd.read_csv(INPUT_FILE)

    print(f"Rows: {len(df):,}")

    return df


import re


def normalize_location(text):
    text = str(text).upper().strip()
    text = re.sub(r"[^A-Z0-9 ]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def create_hotspot_column(df):

    df["hotspot_name"] = np.where(
        df["junction_name"] != "No Junction",
        df["junction_name"],
        df["location"].apply(normalize_location)
    )

    df["hotspot_type"] = np.where(
        df["junction_name"] != "No Junction",
        "JUNCTION",
        "ROAD_SEGMENT"
    )

    return df


def engineer_features(df):

    print("Creating severity score...")

    df["severity_score"] = (
        df["violation_type"]
        .apply(get_severity_score)
    )

    print("Creating vehicle impact score...")

    vehicle_col = df["updated_vehicle_type"].fillna(df["vehicle_type"])
    df["vehicle_score"] = vehicle_col.apply(get_vehicle_score)

    df["date"] = pd.to_datetime(
        df["created_datetime"]
    ).dt.date

    return df


def aggregate_hotspots(df):

    hotspot_df = (
    df
    .groupby("hotspot_name")
    .agg(
        hotspot_type=("hotspot_type", "first"),

        violations=("id", "count"),

        avg_severity=(
            "severity_score",
            "mean"
        ),

        avg_vehicle_impact=(
            "vehicle_score",
            "mean"
        ),

        recurrence_days=(
            "date",
            "nunique"
        ),

        latitude=(
            "latitude",
            "mean"
        ),

        longitude=(
            "longitude",
            "mean"
        )
    )
    .reset_index()
)

    return hotspot_df


def save_data(hotspot_df):

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    hotspot_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"Saved hotspot file -> {OUTPUT_FILE}"
    )


def print_summary(hotspot_df):

    print("\nTOP 10 HOTSPOTS\n")

    print(
        hotspot_df
        .sort_values(
            "violations",
            ascending=False
        )
        [
            [
                "hotspot_name",
                "violations",
                "avg_severity"
            ]
        ]
        .head(10)
    )


def main():

    df = load_data()

    df = create_hotspot_column(df)

    df = engineer_features(df)

    hotspot_df = aggregate_hotspots(df)

    print_summary(hotspot_df)

    save_data(hotspot_df)

    print("\nHotspot calculation complete")


if __name__ == "__main__":
    main()