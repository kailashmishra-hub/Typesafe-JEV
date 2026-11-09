# Typesafe JEV — Customer loan intake demo

Search a synthetic customer, retrieve their records across eight Excel workbooks,
download a loan-focused JSON, and evaluate the same JSON with Typesafe JEV.

## Run (Python 3.10+)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:TYPESAFE_API_KEY = 'your-typesafe-api-key'
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8502
```

Open http://localhost:8502, enter `CUST0001` through `CUST0050`, and click
**Find customer**. The JSON download works without an API key. Click **Evaluate
with JEV** to send the displayed customer's export to Typesafe. Keep your API key
in the server environment, never in Excel, customer JSON, source code or Git.
`.env.example` documents variables; `.env` is not loaded automatically.

## How JEV is integrated

`app.py` calls `build_loan_export` and passes the resulting structured JSON to
`jev_evaluation.evaluate_customer`. That function constructs SDK questions from
`questions.json` and calls `TypeSafeClient(model='jev-latest').system_one`.
`TYPESAFE_MODEL` can override the model. Results retain the API's answer types,
probabilities and confidence in the UI. New searches clear previous assessments.

The three demo questions assess document verification, compliance-review triggers,
and the next intake step. They are evaluated from the source state, not from each
other's answers. The last question applies the explicitly documented demo priorities
in `questions.json`. This is not an underwriting or automatic loan approval system.
No lender eligibility thresholds are provided. A model answer can contradict its
source even with high confidence; compare explicit flags against the records.

For CUST0001, the supplied records support verified documents, no listed compliance
trigger, and sending the intake to an underwriter. Live output is model-dependent;
these are expected test interpretations, not fabricated API results.

## Data and export

All 50 customer records in `data/` are synthetic. Source spreadsheets are read only.
The repository validates the eight workbooks and joins their records by customer ID.
`CUSTOMER_DATA_DIR` can point to an alternative folder with the same schema.

The export contains 13 sections. Transactions cover the latest 12 complete available
statement months (November 2025–October 2026 in this dataset). Detailed records
include amounts **strictly above INR 100,000**, returned payments and AML-linked
transactions regardless of amount. Exactly INR 100,000 needs an exception to qualify.
The selection applies to both credits and debits and deduplicates overlapping reasons.
The INR cutoff is a detail filter, not an AML or credit risk rule.

`summary.transaction_activity` includes all transactions in that year before detail
filtering. An empty filtered list is not evidence of no activity. `banking_monthly`
retains 60 months in a compact `columns`/`rows` table. Other sections remain lists.
Repeated IDs, provenance and selected administrative metadata are omitted; this is a
loan-focused projection, not a lossless full-source copy. Command-line retrieval
through `customer_lookup.py` retains the complete source schema.

For CUST0001 the detailed export contains 12 transactions, while yearly totals cover
120. Large requests can still exceed provider limits; failures never silently trim
the state or fabricate results. Evaluation is a user-triggered external API call.

## Tests

```powershell
python -m unittest discover -s tests -v
```

Tests use a fake client, require no API key or paid API calls, and check the real SDK
question construction, preserved request state, missing-key handling and export rules.

Reference: https://docs.typesafe.ai/introduction/quickstart
