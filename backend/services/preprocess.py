import pandas as pd
from pathlib import Path


RAW_FILE = Path("data/raw/jan_to_may_police_violations.csv")
OUTPUT_FILE = Path("data/processed/cleaned.csv")


def load_data():
    """
    Load raw dataset
    """
    print("Loading dataset...")

    df = pd.read_csv(RAW_FILE)

    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    return df


def filter_invalid_validation(df):
    """Drop records the source system marked rejected/duplicate"""
    before = len(df)
    df = df[~df["validation_status"].isin(["rejected", "duplicate"])]
    print(f"Removed {before - len(df):,} rejected/duplicate rows")
    return df


def remove_duplicates(df):
    """
    Remove duplicate records
    """

    before = len(df)

    df = df.drop_duplicates()

    after = len(df)

    print(f"Removed {before - after:,} duplicate rows")

    return df


def drop_unidentifiable_rows(df):
    """Drop rows with no location AND no junction - nothing to group by"""
    before = len(df)
    no_location = df["location"].isna()
    no_junction = df["junction_name"].isna() | (df["junction_name"] == "No Junction")
    df = df[~(no_location & no_junction)]
    print(f"Removed {before - len(df):,} rows with no location and no junction")
    return df


def clean_coordinates(df):
    """
    Remove invalid coordinates
    """

    before = len(df)

    df = df.dropna(subset=["latitude", "longitude"])

    df = df[
        (df["latitude"].between(-90, 90))
        & (df["longitude"].between(-180, 180))
    ]

    after = len(df)

    print(f"Removed {before - after:,} rows with invalid coordinates")

    return df


def process_datetime(df):
    """
    Convert datetime and extract features
    """

    df["created_datetime"] = pd.to_datetime(
        df["created_datetime"],
        errors="coerce"
    )

    df = df.dropna(subset=["created_datetime"])

    df["hour"] = df["created_datetime"].dt.hour

    df["day"] = df["created_datetime"].dt.day_name()

    df["month"] = df["created_datetime"].dt.month_name()

    df["is_weekend"] = (
        df["created_datetime"]
        .dt.dayofweek
        .isin([5, 6])
    )

    return df


def clean_text_columns(df):
    """
    Standardize text fields
    """

    text_cols = [
        "violation_type",
        "vehicle_type",
        "junction_name",
        "location"
    ]

    for col in text_cols:

        if col in df.columns:

            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
            )

    return df


def generate_summary(df):

    print("\nDATA SUMMARY")
    print("=" * 50)

    print(f"Rows: {len(df):,}")

    print(
        f"Unique Locations: "
        f"{df['location'].nunique():,}"
    )

    print(
        f"Unique Junctions: "
        f"{df['junction_name'].nunique():,}"
    )

    print(
        f"Unique Violation Types: "
        f"{df['violation_type'].nunique():,}"
    )

    print(
        f"Unique Vehicle Types: "
        f"{df['vehicle_type'].nunique():,}"
    )

    print("\nTop Violations:")

    print(
        df["violation_type"]
        .value_counts()
        .head(10)
    )

    print("\nTop Junctions:")

    print(
        df["junction_name"]
        .value_counts()
        .head(10)
    )


def save_data(df):

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(f"\nSaved to: {OUTPUT_FILE}")


def main():

    df = load_data()

    df = filter_invalid_validation(df)

    df = remove_duplicates(df)

    df = clean_coordinates(df)

    df = drop_unidentifiable_rows(df)

    df = process_datetime(df)

    df = clean_text_columns(df)

    generate_summary(df)

    save_data(df)

    print("\nPreprocessing Complete")


if __name__ == "__main__":
    main()