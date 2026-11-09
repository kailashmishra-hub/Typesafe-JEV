# Typesafe JEV — Terminal customer lookup

Enter a CustomerID, see customer details, save customer JSON, and optionally evaluate
the same JSON with Typesafe JEV. All 50 demo customers are synthetic.

## Run

Requires Python 3.10 or later. Open a terminal in this repository folder:

```powershell
python -m pip install -r requirements.txt
python console_app.py
```

Enter `CUST0001` (or any ID through `CUST0050`). The program displays basic customer
information and saves `exports/CUST0001_loan_details.json`.

## Optional JEV evaluation

Set your key in the same PowerShell window before running:

```powershell
$env:TYPESAFE_API_KEY = 'your-typesafe-api-key'
python console_app.py
```

After lookup, enter `y` to send the customer JSON to Typesafe. The program prints
the actual API response and saves `exports/CUST0001_jev_result.json`.
Without a key, or if you decline, customer retrieval and export still work.
Never commit API keys. `.env.example` documents variables; `.env` is not loaded
automatically. `TYPESAFE_MODEL` can override the default `jev-latest` model.

## Files

| File | Purpose |
|---|---|
| `console_app.py` | Main program: customer prompt, details and output files |
| `customer_lookup.py` | Read and join customer records from Excel |
| `loan_export.py` | Build the loan-focused customer JSON |
| `jev_evaluation.py` | Call the Typesafe Python SDK |
| `questions.json` | Document verification, compliance and next-step questions |
| `data/` | Eight Excel workbooks containing 50 synthetic customers |
| `requirements.txt` | Required Python packages |
| `tests/` | Local tests; no paid API calls |

## Customer JSON

All 13 customer sections are included. Transaction details cover the latest 12
complete available statement months: November 2025–October 2026 in this dataset.
Details include amounts strictly above INR 100,000, plus returned payments and
AML-linked transactions regardless of amount, within that year. Summary totals
cover all transactions in the year before filtering. For CUST0001, this means
12 detailed transactions and totals covering 120 transactions. The cutoff selects
detail; it is not a lending or AML risk rule.

Monthly banking retains 60 months as a compact `columns`/`rows` table. Other sections
are lists. Administrative metadata and repeated fields are omitted; this export
is not a lossless copy of the spreadsheets. Source workbooks are read only.
`CUSTOMER_DATA_DIR` can specify another folder with the same workbook schema.

JEV receives the export as state and the questions in `questions.json`. Results
are intake assessments, not loan approvals. Verify explicit source flags even
when model confidence is high. Failed requests do not silently trim the data.

## Tests

```powershell
python -m unittest discover -s tests -v
```

Reference: https://docs.typesafe.ai/introduction/quickstart
