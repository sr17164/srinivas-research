# Data sources

The original project used the following sources. URLs are provided for traceability.

| Series | Role | Source |
|---|---|---|
| XLE adjusted prices | US energy-equity proxy | https://finance.yahoo.com/quote/XLE/ |
| XME adjusted prices | US metals-and-mining equity proxy | https://finance.yahoo.com/quote/XME/ |
| Brent futures | Oil-price proxy | https://finance.yahoo.com/quote/BZ%3DF/ |
| Gold futures | Gold-price proxy | https://finance.yahoo.com/quote/GC%3DF/ |
| Copper futures | Copper-price proxy | https://finance.yahoo.com/quote/HG%3DF/ |
| 10-year Treasury yield (DGS10) | Interest-rate control | https://fred.stlouisfed.org/series/DGS10 |
| Consumer Price Index (CPIAUCSL) | Headline inflation regime | https://fred.stlouisfed.org/series/CPIAUCSL |
| Sticky Price CPI (CORESTICKM159SFRBATL) | Inflation context | https://fred.stlouisfed.org/series/CORESTICKM159SFRBATL |

The FRED CSV files retained from the original project are included under `data/raw/`. The original adjusted-close market data were not retained, so the packaged analysis starts from the original prepared return dataset and explicitly documents that limitation.
