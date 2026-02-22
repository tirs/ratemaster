# Sample CSV Data for Testing

Use these files to test the Data Ingestion and YoY flows.

## Files

| File | Use for | Date range |
|------|---------|------------|
| `sample-current-data.csv` | **Current Data** upload | Feb 2025 |
| `sample-prior-year-data.csv` | **Prior Year (YoY)** upload | Feb 2024 |

## How to use

1. Log in and go to **Dashboard → Data Ingestion**
2. Select a property
3. **Current Data**: Drag & drop `sample-current-data.csv` or click "Select File" in the left card
4. **Prior Year (YoY)**: Drag & drop `sample-prior-year-data.csv` or click "Select File" in the right card

## Columns (auto-detected)

- `stay_date` – required
- `booking_date` – optional, enables lead-time patterns
- `rooms_available`, `total_rooms`, `rooms_sold`
- `adr`, `total_rate`, `revenue`

## YoY comparison

The prior year file has the same structure but dates shifted back one year. This lets the engine compute YoY trend curves by season, day-of-week, and lead-time bucket.
