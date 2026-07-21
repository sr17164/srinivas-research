# Methodology

## Objective

The project tests whether the sensitivity of commodity-producer equity returns to underlying commodity returns changes when inflation is elevated.

## Retained data

The retained prepared dataset covers April 2017 to December 2025 and contains monthly returns for Brent crude, gold, copper, the Energy Select Sector SPDR Fund (XLE) and the SPDR S&P Metals & Mining ETF (XME), together with the US 10-year Treasury yield, headline CPI inflation and Atlanta Fed Sticky CPI.

The original adjusted-close series downloaded from Yahoo Finance were not retained. The revised project therefore reproduces the analysis from the prepared return dataset rather than rebuilding every return from raw market prices.

## Data-quality correction

The original workflow forward-filled missing monthly futures prices and then calculated percentage returns. That procedure generated rows in which Brent, gold and copper returns were all exactly zero despite non-zero XLE and XME returns. The current exclusion count is generated from the data-quality log rather than maintained in this narrative. These rows were excluded because they mechanically attenuate commodity-equity relationships and are not credible observations of three futures contracts all being unchanged in the same month.

Lagged CPI and the monthly change in the Treasury yield are calculated on the full chronological dataset before exclusions. This preserves the intended one-month information lag where observations are available.

## Primary regime definition

A month is classified as high inflation when the previous month's year-on-year headline CPI inflation rate is at least 3.0%. Lagging the regime variable avoids using the current month's inflation reading to classify the same month's market return.

## Regression specification

Two full-sample models are estimated:

- XLE monthly return as the dependent variable.
- XME monthly return as the dependent variable.

Each model includes:

- Brent return
- gold return
- copper return
- high-inflation indicator
- Brent × high-inflation interaction
- gold × high-inflation interaction
- copper × high-inflation interaction
- monthly change in the US 10-year Treasury yield

The lower-inflation commodity beta is the base coefficient. The high-inflation beta is the base coefficient plus the relevant interaction coefficient. The p-value on the interaction tests whether the two regime betas differ.

Newey-West/HAC standard errors with three lags are used to reduce sensitivity to heteroskedasticity and short-run serial correlation.

## Robustness

The same model is re-estimated using lagged headline CPI thresholds of 2.68%, 3.0%, 3.5% and 4.0%. The 2.68% threshold is the median of the available lagged headline-CPI series before the model exclusions, providing a natural even-split benchmark alongside the three round-number thresholds. This checks whether the result depends on a single regime boundary.

## Limitations

- The current usable sample size is generated directly from the audited model dataset and reported in the output summary.
- The retained market dataset is already transformed into returns.
- ETFs are imperfect proxies for producer economics and contain company-specific exposures.
- Futures returns include financial-market effects that may not track contemporaneous physical prices.
- The model identifies conditional associations, not causal effects.
- Threshold selection remains a modelling choice.
- Multiple hypothesis testing can produce isolated significant findings.
## Predictive limitation

The regressions are contemporaneous sensitivity estimates: commodity and producer-equity returns are measured in the same month. They test whether the historical relationship differs across inflation regimes, not whether commodity returns predict future equity returns. Any trading-signal extension would require lagged features, walk-forward or other out-of-sample evaluation, and explicit transaction-cost assumptions.

