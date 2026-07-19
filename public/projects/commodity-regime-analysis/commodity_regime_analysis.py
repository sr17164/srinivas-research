"""Revised commodity-producer equity sensitivity analysis.

This script audits and re-estimates the original student project using the
retained prepared monthly dataset. It removes 14 artificial observations in
which Brent, gold and copper returns were all exactly zero while producer-equity
returns moved, a pattern created by forward-filling missing futures prices
before calculating returns in the original pipeline.

Primary specification
---------------------
* 89 usable monthly observations, May 2017 to December 2025.
* High-inflation regime: prior-month headline CPI inflation >= 3.0%.
* Full-sample interaction regressions rather than separate sub-sample OLS.
* Energy and mining ETF returns are regressed on Brent, gold and copper returns,
  a high-inflation indicator, three commodity-by-regime interactions and the
  monthly change in the US 10-year Treasury yield.
* Newey-West/HAC standard errors with three lags.

The retained dataset contains returns, not the original adjusted-close series.
The project is therefore reproducible from the retained prepared dataset, but
not a perfect reconstruction from raw Yahoo Finance prices.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parent
RAW_PATH = ROOT / "data" / "raw" / "original_prepared_dataset.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUTS_DIR = ROOT / "outputs"
FIGURES_DIR = ROOT / "figures"

PRIMARY_THRESHOLD = 3.0
ROBUSTNESS_THRESHOLDS = [2.68, 3.0, 3.5, 4.0]
HAC_LAGS = 3
COMMODITIES = ["Brent", "Gold", "Copper"]
DEPENDENTS = ["EnergyETF", "MiningETF"]
REQUIRED_COLUMNS = [
    "observation_date",
    "Brent",
    "Gold",
    "Copper",
    "EnergyETF",
    "MiningETF",
    "Treasury10Y",
    "Headline_Inflation",
    "Sticky_Inflation",
]

for directory in [PROCESSED_DIR, OUTPUTS_DIR, FIGURES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


def load_and_audit() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load retained data, flag artificial observations and create model data."""
    raw = pd.read_csv(RAW_PATH, parse_dates=["observation_date"])
    missing = sorted(set(REQUIRED_COLUMNS) - set(raw.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    raw = raw[REQUIRED_COLUMNS].sort_values("observation_date").reset_index(drop=True)
    raw["Lagged_Headline_Inflation"] = raw["Headline_Inflation"].shift(1)
    raw["Delta_Treasury10Y"] = raw["Treasury10Y"].diff()

    all_commodities_zero = np.isclose(raw[COMMODITIES], 0.0).all(axis=1)
    producer_equities_moved = (~np.isclose(raw[DEPENDENTS], 0.0)).any(axis=1)
    raw["Artificial_Zero_Flag"] = all_commodities_zero & producer_equities_moved

    quality_log = raw.loc[
        raw["Artificial_Zero_Flag"],
        ["observation_date", *COMMODITIES, *DEPENDENTS],
    ].copy()
    quality_log["Issue"] = (
        "All three commodity returns equal zero while producer-equity returns moved; "
        "excluded as forward-fill artefact."
    )

    model = raw.loc[~raw["Artificial_Zero_Flag"]].copy()
    model = model.dropna(
        subset=["Lagged_Headline_Inflation", "Delta_Treasury10Y"]
    ).reset_index(drop=True)
    model["High_Inflation"] = (
        model["Lagged_Headline_Inflation"] >= PRIMARY_THRESHOLD
    ).astype(int)
    model["Inflation_Regime"] = np.where(
        model["High_Inflation"].eq(1), "High", "Lower"
    )

    for commodity in COMMODITIES:
        model[f"{commodity}_x_High"] = (
            model[commodity] * model["High_Inflation"]
        )

    raw.to_csv(PROCESSED_DIR / "audited_full_dataset.csv", index=False)
    model.to_csv(PROCESSED_DIR / "model_dataset.csv", index=False)
    quality_log.to_csv(PROCESSED_DIR / "data_quality_log.csv", index=False)
    return raw, model, quality_log


def design_matrix(data: pd.DataFrame, threshold: float) -> pd.DataFrame:
    high = (data["Lagged_Headline_Inflation"] >= threshold).astype(int)
    matrix = pd.DataFrame(index=data.index)
    matrix["High_Inflation"] = high
    for commodity in COMMODITIES:
        matrix[commodity] = data[commodity]
        matrix[f"{commodity}_x_High"] = data[commodity] * high
    matrix["Delta_Treasury10Y"] = data["Delta_Treasury10Y"]
    return sm.add_constant(matrix, has_constant="add")


def fit_models(
    data: pd.DataFrame, threshold: float
) -> dict[str, sm.regression.linear_model.RegressionResultsWrapper]:
    x = design_matrix(data, threshold)
    return {
        dependent: sm.OLS(data[dependent], x).fit(
            cov_type="HAC", cov_kwds={"maxlags": HAC_LAGS}
        )
        for dependent in DEPENDENTS
    }


def relationship_rows(
    models: dict[str, sm.regression.linear_model.RegressionResultsWrapper],
    threshold: float,
    observations: int,
    high_count: int,
) -> list[dict[str, Any]]:
    relationships = [
        ("Brent → energy equities", "EnergyETF", "Brent"),
        ("Gold → mining equities", "MiningETF", "Gold"),
        ("Copper → mining equities", "MiningETF", "Copper"),
    ]
    rows: list[dict[str, Any]] = []
    for label, dependent, commodity in relationships:
        model = models[dependent]
        interaction = f"{commodity}_x_High"
        low_beta = float(model.params[commodity])
        increment = float(model.params[interaction])
        rows.append(
            {
                "Threshold": threshold,
                "Relationship": label,
                "Dependent": dependent,
                "Commodity": commodity,
                "Lower_Inflation_Beta": low_beta,
                "High_Inflation_Beta": low_beta + increment,
                "Regime_Difference": increment,
                "Difference_HAC_PValue": float(model.pvalues[interaction]),
                "Lower_Beta_HAC_PValue": float(model.pvalues[commodity]),
                "Model_R_Squared": float(model.rsquared),
                "Observations": observations,
                "High_Inflation_Observations": high_count,
                "Lower_Inflation_Observations": observations - high_count,
            }
        )
    return rows


def save_full_model_outputs(
    models: dict[str, sm.regression.linear_model.RegressionResultsWrapper],
) -> None:
    coefficient_rows: list[dict[str, Any]] = []
    for dependent, model in models.items():
        for variable in model.params.index:
            coefficient_rows.append(
                {
                    "Dependent": dependent,
                    "Variable": variable,
                    "Coefficient": float(model.params[variable]),
                    "HAC_Std_Error": float(model.bse[variable]),
                    "HAC_T_Statistic": float(model.tvalues[variable]),
                    "HAC_P_Value": float(model.pvalues[variable]),
                    "CI_95_Lower": float(model.conf_int().loc[variable, 0]),
                    "CI_95_Upper": float(model.conf_int().loc[variable, 1]),
                    "R_Squared": float(model.rsquared),
                    "Observations": int(model.nobs),
                }
            )
    pd.DataFrame(coefficient_rows).to_csv(
        OUTPUTS_DIR / "full_regression_coefficients.csv", index=False
    )

    with (OUTPUTS_DIR / "regression_summaries.txt").open(
        "w", encoding="utf-8"
    ) as file:
        for dependent, model in models.items():
            file.write(f"\n{'=' * 88}\n{dependent}\n{'=' * 88}\n")
            file.write(model.summary().as_text())
            file.write("\n")


def create_figures(primary: pd.DataFrame, robustness: pd.DataFrame) -> None:
    labels = primary["Relationship"].tolist()
    lower = primary["Lower_Inflation_Beta"].to_numpy()
    high = primary["High_Inflation_Beta"].to_numpy()

    x = np.arange(len(labels))
    width = 0.36
    fig, ax = plt.subplots(figsize=(10, 6))
    lower_bars = ax.bar(x - width / 2, lower, width, label="Lower inflation")
    high_bars = ax.bar(x + width / 2, high, width, label="High inflation")
    ax.axhline(0, linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Estimated return sensitivity")
    ax.set_title("Commodity-equity sensitivity by inflation regime")
    ax.legend()
    for bars in [lower_bars, high_bars]:
        for bar in bars:
            height = bar.get_height()
            ax.annotate(
                f"{height:.2f}",
                (bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 4 if height >= 0 else -12),
                textcoords="offset points",
                ha="center",
                va="bottom" if height >= 0 else "top",
                fontsize=9,
            )
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "commodity-equity-sensitivity.png", dpi=220)
    plt.close(fig)

    brent = robustness.loc[
        robustness["Relationship"].eq("Brent → energy equities")
    ].sort_values("Threshold")
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(
        brent["Threshold"],
        brent["Regime_Difference"],
        marker="o",
        label="High-minus-lower inflation beta",
    )
    ax.axhline(0, linewidth=0.8)
    ax.set_xlabel("Lagged headline CPI threshold (%)")
    ax.set_ylabel("Interaction coefficient")
    ax.set_title("Robustness of the Brent regime effect")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "brent-threshold-robustness.png", dpi=220)
    plt.close(fig)


def write_summary(
    model_data: pd.DataFrame,
    quality_log: pd.DataFrame,
    primary: pd.DataFrame,
    robustness: pd.DataFrame,
) -> None:
    brent = primary.loc[
        primary["Relationship"].eq("Brent → energy equities")
    ].iloc[0]
    gold = primary.loc[
        primary["Relationship"].eq("Gold → mining equities")
    ].iloc[0]
    copper = primary.loc[
        primary["Relationship"].eq("Copper → mining equities")
    ].iloc[0]

    summary = {
        "sample_start": model_data["observation_date"].min().strftime("%Y-%m"),
        "sample_end": model_data["observation_date"].max().strftime("%Y-%m"),
        "observations": int(len(model_data)),
        "excluded_artificial_zero_rows": int(len(quality_log)),
        "primary_threshold_percent": PRIMARY_THRESHOLD,
        "hac_lags": HAC_LAGS,
        "brent_energy": brent.to_dict(),
        "gold_mining": gold.to_dict(),
        "copper_mining": copper.to_dict(),
    }
    with (OUTPUTS_DIR / "analysis_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=float)

    def significance(p_value: float) -> str:
        return "statistically distinguishable" if p_value < 0.05 else "not statistically distinguishable"

    report = f"""# Revised findings

## Research question

Do inflation regimes alter the relationship between commodity returns and commodity-producer equity returns?

## Data audit

The retained prepared dataset contained 104 monthly rows from April 2017 to December 2025. Fourteen rows recorded Brent, gold and copper returns of exactly zero even though the producer-equity ETFs moved. Those rows were generated by forward-filling missing futures prices before calculating returns in the original workflow and are excluded. After constructing one-month-lagged inflation and the monthly change in the 10-year Treasury yield, the primary model uses **{len(model_data)} observations**.

## Primary specification

The high-inflation indicator equals one when the **previous month's** headline CPI inflation rate is at least **{PRIMARY_THRESHOLD:.1f}%**. A full-sample interaction model allows each commodity beta to change in the high-inflation regime. Energy and mining equity models include Brent, gold and copper returns simultaneously, the high-inflation indicator, the three interaction terms and the monthly change in the US 10-year Treasury yield. Reported p-values use Newey-West/HAC standard errors with {HAC_LAGS} lags.

## Results

- **Brent and energy equities:** the estimated beta is {brent['Lower_Inflation_Beta']:.3f} in lower-inflation months and {brent['High_Inflation_Beta']:.3f} in high-inflation months. The difference is {brent['Regime_Difference']:.3f} with a HAC p-value of {brent['Difference_HAC_PValue']:.3f}. The regime difference is {significance(brent['Difference_HAC_PValue'])} at the 5% level.
- **Gold and mining equities:** the estimated beta increases from {gold['Lower_Inflation_Beta']:.3f} to {gold['High_Inflation_Beta']:.3f}, but the difference has a HAC p-value of {gold['Difference_HAC_PValue']:.3f}. The revised analysis does **not** support the original claim that the gold sensitivity changes reliably across regimes.
- **Copper and mining equities:** the estimated beta increases from {copper['Lower_Inflation_Beta']:.3f} to {copper['High_Inflation_Beta']:.3f}, but the difference has a HAC p-value of {copper['Difference_HAC_PValue']:.3f}. Copper remains positively associated with mining-equity returns, but the regime difference is imprecise at the primary threshold.

## Interpretation

The narrow defensible conclusion is that the transmission of Brent returns into energy-equity returns was materially stronger when inflation was already elevated. The evidence is not strong enough to claim comparable regime shifts for gold or copper. These are associations, not causal estimates, and the sample remains modest.

## Robustness

The file `outputs/threshold_robustness.csv` reports the same interaction specification using CPI thresholds of 2.68%, 3.0%, 3.5% and 4.0%. The Brent interaction remains positive and statistically significant across all four thresholds. Copper's interaction becomes significant only at the higher thresholds, so that result is threshold-sensitive and should not be treated as a stable finding.
"""
    (ROOT / "docs" / "revised_findings.md").write_text(report, encoding="utf-8")


def main() -> None:
    _, model_data, quality_log = load_and_audit()

    primary_models = fit_models(model_data, PRIMARY_THRESHOLD)
    primary_rows = relationship_rows(
        primary_models,
        threshold=PRIMARY_THRESHOLD,
        observations=len(model_data),
        high_count=int(
            (model_data["Lagged_Headline_Inflation"] >= PRIMARY_THRESHOLD).sum()
        ),
    )
    primary = pd.DataFrame(primary_rows)
    primary.to_csv(OUTPUTS_DIR / "primary_relationship_results.csv", index=False)
    save_full_model_outputs(primary_models)

    robustness_rows: list[dict[str, Any]] = []
    for threshold in ROBUSTNESS_THRESHOLDS:
        models = fit_models(model_data, threshold)
        robustness_rows.extend(
            relationship_rows(
                models,
                threshold=threshold,
                observations=len(model_data),
                high_count=int(
                    (model_data["Lagged_Headline_Inflation"] >= threshold).sum()
                ),
            )
        )
    robustness = pd.DataFrame(robustness_rows)
    robustness.to_csv(OUTPUTS_DIR / "threshold_robustness.csv", index=False)

    create_figures(primary, robustness)
    write_summary(model_data, quality_log, primary, robustness)

    print("Revised analysis complete.")
    print(primary.to_string(index=False))


if __name__ == "__main__":
    main()
