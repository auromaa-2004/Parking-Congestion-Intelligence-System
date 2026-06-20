import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler

INPUT_FILE = Path("data/processed/hotspot_scores.csv")
OUTPUT_FILE = Path("data/processed/ranked_zones.csv")


def load_data():

    print("Loading hotspot data...")

    df = pd.read_csv(INPUT_FILE)

    print(f"Total hotspots before filtering: {len(df):,}")

    return df


def filter_hotspots(df):

    MIN_VIOLATIONS = 50

    before = len(df)

    df = df[
        df["violations"] >= MIN_VIOLATIONS
    ].copy()

    after = len(df)

    print(
        f"Filtered hotspots "
        f"({before:,} -> {after:,}) "
        f"using violations >= {MIN_VIOLATIONS}"
    )

    return df


def normalize_features(df):

    scaler = MinMaxScaler()
    df["violations_log"] = np.log1p(
        df["violations"]
    )

    cols = [
        "violations_log",
        "avg_severity",
        "avg_vehicle_impact",
        "recurrence_days"
    ]

    normalized = scaler.fit_transform(
        df[cols]
    )

    df["violations_norm"] = normalized[:, 0] * 100
    df["severity_norm"] = normalized[:, 1] * 100
    df["vehicle_norm"] = normalized[:, 2] * 100
    df["recurrence_norm"] = normalized[:, 3] * 100

    return df


def calculate_risk_score(df):

    df["risk_score"] = (

        0.80 * df["violations_norm"]

        + 0.10 * df["severity_norm"]

        + 0.05 * df["recurrence_norm"]

        + 0.05 * df["vehicle_norm"]

    )

    return df


def create_rankings(df):

    df = df.sort_values(
        "risk_score",
        ascending=False
    ).reset_index(drop=True)

    df["rank"] = df.index + 1

    return df


def assign_priority(df):

    q90, q70, q40, q15 = df["risk_score"].quantile(
        [0.90, 0.70, 0.40, 0.15]
    )

    df["priority"] = np.select(
        [
            df["risk_score"] >= q90,
            df["risk_score"] >= q70,
            df["risk_score"] >= q40,
            df["risk_score"] >= q15
        ],
        [
            "CRITICAL",
            "HIGH",
            "MEDIUM",
            "LOW"
        ],
        default="VERY LOW"
    )

    return df


def generate_recommendation(df):

    text_map = {
        "CRITICAL": "Immediate enforcement deployment required",
        "HIGH": "High priority enforcement zone",
        "MEDIUM": "Regular patrol recommended",
        "LOW": "Periodic monitoring recommended",
        "VERY LOW": "Low enforcement priority"
    }

    df["recommendation"] = df["priority"].map(text_map)

    return df


def save_data(df):

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(f"\nSaved -> {OUTPUT_FILE}")


def print_summary(df):

    print("\nTOP 20 ENFORCEMENT ZONES\n")

    cols = [
        "rank",
        "hotspot_name",
        "violations",
        "risk_score",
        "priority"
    ]

    print(
        df[cols]
        .head(20)
        .to_string(index=False)
    )

    print("\n")

    print(
        "Priority Distribution:"
    )

    print(
        df["priority"]
        .value_counts()
    )


def main():

    df = load_data()

    df = filter_hotspots(df)

    df = normalize_features(df)

    df = calculate_risk_score(df)

    df = create_rankings(df)

    df = assign_priority(df)

    df = generate_recommendation(df)

    print_summary(df)

    save_data(df)

    print("\nRisk scoring complete.")


if __name__ == "__main__":
    main()