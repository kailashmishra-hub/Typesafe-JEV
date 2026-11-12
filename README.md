# Typesafe JEV customer lookup

## Retrieve a customer

Run in the repository folder:

```powershell
python console_app.py
```

Enter the exact CustomerID, for example `CUST0001`.
The program looks in `data/customers.json` first, then reads the other JSON files
in `data/` and collects every record with that CustomerID. It prints the customer
profile and saves `exports/CUST0001_loan_details.json`.

No extra packages are needed for this lookup. There are no format checks,
relationship checks, risk calculations, date filters or amount filters.
All source field names and values are kept, including CustomerID on every record,
metadata, nulls and full transaction history. A customer with no records in a file
gets an empty list for that section. An unknown ID prints `Customer not found.`

The output uses `sections.customer_profile` for matching customers.json records.
Each other section uses its JSON filename, without `.json`:

```json
{
  "sections": {
    "customer_profile": [{"CustomerID": "CUST0001", "DisplayName": "..."}],
    "employment_income": [],
    "transactions": []
  }
}
```

These are container names only; the original column names inside every record
are unchanged. Banking monthly records are ordinary objects, not compact arrays.
There are no generated summary or provenance sections.

## Source files

`data/` contains 13 JSON lists covering 50 synthetic customers. These were exported
once from the eight existing demo Excel workbooks, using their original headers.
Excel dates are represented as ISO text for JSON. The program itself only reads JSON.
Edit or replace these JSON lists when the source data changes; the console does
not convert Excel on each lookup. New data files should be lists of records with
an exact `CustomerID` field.

## Evaluate with JEV separately

`run_jev.py` reads a customer export and `questions.json`, loads the API key from
`.env`, and sends `model`, `state` and `questions` to Typesafe. Install its dependency:

```powershell
python -m pip install python-dotenv
python run_jev.py
```

Set `TYPESAFE_API_KEY=your-key` in `.env`. Update the customer export path in
`run_jev.py` to the ID you just retrieved. Results print and save to `response.json`.
The console lookup itself makes no API calls. Questions must refer to the source
fields in `sections`; banking_monthly now contains objects with original headers.

`jev_evaluation.py` remains the standalone sender for an existing complete
`request.json`. Keep actual API keys out of Git.
