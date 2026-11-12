# Customer lookup from Excel

## Run

Keep the eight Excel workbooks in `data/`, then run:

```powershell
python -m pip install -r requirements.txt
python console_app.py
```

Enter a CustomerID such as `CUST0001`. The program reads the Excel files directly,
collects the matching rows from each worksheet containing a CustomerID column,
prints the customer profile and saves `exports/CUST0001_loan_details.json`.
The same lookup applies to every CustomerID. The console prints the number of
records exported from each worksheet, including the complete transaction count.
Run it again with another ID to create that customer's own export file.

No customer or source JSON files are created upfront. There is no separate
conversion step. Every lookup reads the current workbook contents.
All matching rows and original column names are retained. No transaction filters,
field trimming, computed summaries or extra validation are applied. Excel dates
are written as text because JSON has no native date type.

Output is grouped under `sections` using the original worksheet names, for example
`Customers`, `EmploymentIncome`, `Transactions` and `KYCHistory`. Each section is
an array of records using the exact Excel column headers. Worksheets without a
CustomerID column, such as Guide and FieldDictionary, are skipped.

## JEV separately

`run_jev.py` sends the customer export and the separate `questions.json` to JEV.
Set your key in `.env` as `TYPESAFE_API_KEY=your-key`. Update the export filename
in that script for your selected customer, then run `python run_jev.py`.
Question instructions should use the output's worksheet names, such as
`sections.Documents` and `sections.ScreeningHistory`.
The customer lookup itself does not call JEV.
