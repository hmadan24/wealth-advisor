# Sample Portfolio Excel Format

Create an Excel file (.xlsx) with the following columns:

## Required Columns:
| Column Name | Description | Example |
|-------------|-------------|---------|
| Scheme Name | Name of stock/fund | "HDFC Bank Ltd" |
| Units | Number of shares/units | 100 |
| Purchase NAV | Price at which you bought | 1450.50 |
| Current NAV | Current market price | 1620.75 |

## Optional Columns:
| Column Name | Description | Example |
|-------------|-------------|---------|
| ISIN | ISIN code | INE040A01034 |
| Asset Type | Equity/MF/Debt/Gold | "Equity" |
| Broker | Broker/AMC name | "Zerodha" |
| Folio | Account/Folio number | "12345678" |
| Purchase Date | When you bought | 2023-01-15 |

## Alternative Format (Pre-calculated):
Instead of NAVs, you can provide:
- **Invested Amount**: Total cost (Units × Purchase Price)
- **Current Value**: Total value (Units × Current Price)

## Sample Data:

| Scheme Name | Units | Purchase NAV | Current NAV | Asset Type | Broker |
|-------------|-------|--------------|-------------|------------|--------|
| HDFC Bank Ltd | 50 | 1450.50 | 1620.75 | Equity | Zerodha |
| Reliance Industries | 25 | 2380.00 | 2890.50 | Equity | Zerodha |
| Axis Bluechip Fund | 500.5 | 45.20 | 52.80 | MF | Groww |
| ICICI Pru Liquid Fund | 100 | 320.00 | 325.50 | Debt | ICICI |
| SBI Gold Fund | 200 | 18.50 | 21.20 | Gold | SBI MF |

## Column Name Variations Accepted:
The parser is flexible and accepts these variations:
- **Scheme Name**: "Name", "Stock", "Fund Name", "Security"
- **Units**: "Shares", "Quantity", "Qty", "Balance"
- **Purchase NAV**: "Avg Price", "Cost Price", "Buy Price"
- **Current NAV**: "LTP", "CMP", "Market Price", "Price"

