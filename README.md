# Simple Typesafe JEV request

Four files. No Excel lookup, web UI, SDK or extra packages.

- `request.json`: your supplied model, customer state and seven questions.
- `run_jev.py`: sends that JSON to Typesafe and prints/saves the response.
- `README.md`: these instructions.
- `.gitignore`: excludes credentials and generated responses.

## Run in PowerShell (Python 3.10+)

Open a terminal in this folder:

```powershell
$env:TYPESAFE_API_KEY = 'your-typesafe-api-key'
python run_jev.py
```

The response appears in the terminal and is saved to `response.json`. Failed calls
do not overwrite an existing response, so an old file is not a new assessment.
No CustomerID prompt: edit `request.json` to change the customer data or questions.
The program sends the complete request without dropping fields or calculating answers.
Never put your API key inside the request JSON or commit it.

Check the JSON locally without calling the API:

```powershell
python run_jev.py --dry-run
```

Or supply another request file: `python run_jev.py another_request.json`.

## Review the supplied request

The attachment is preserved as supplied, including `model: typesafe/jev-1.14`.
Use a model name available to your direct Typesafe API account if that name is rejected;
the official quickstart uses `jev-latest`. Local dry-run checks JSON structure only,
not model availability or the full API schema.

`identity_status` contains `yes`/`no` fields. The direct API documents optional
`criteria: {"true": "...", "false": "..."}` instead. Its PEP question also differs
from its descriptions about bad records; decide the intended question before editing.
The script warns about this but does not silently change your request or meanings.

References:
- https://docs.typesafe.ai/introduction/quickstart
- https://docs.typesafe.ai/primitives/noul
