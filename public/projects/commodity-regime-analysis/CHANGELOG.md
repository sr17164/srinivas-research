# Changelog

## Revised release

- Identified and excluded 14 artificial zero-return observations created by forward-filling futures prices before return calculation.
- Reduced the usable sample from the originally reported 103 regression observations to 89 correctly specified observations.
- Replaced contemporaneous median-based regime classification with a prior-month 3% headline CPI threshold.
- Replaced separate high- and low-regime regressions with full-sample interaction models.
- Added Newey-West/HAC standard errors with three lags.
- Added robustness tests across four inflation thresholds.
- Withdrew the original claim that gold sensitivity changes reliably in high-inflation regimes.
- Narrowed the conclusion to the robust Brent-to-energy-equity regime effect.
- Added a data-quality log, source documentation and spreadsheet review model.
