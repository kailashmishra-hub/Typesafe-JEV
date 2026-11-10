# Simple Typesafe JEV request

Four files. No Excel lookup, web UI, SDK or extra packages.

- `request.json`: your supplied model, customer state and seven questions.
- `jev_evaluation.py`: sends that JSON to Typesafe and prints/saves the response.
- `README.md`: these instructions.
- `.gitignore`: excludes credentials and generated responses.

## Run in PowerShell (Python 3.10+)

Replace `your-typesafe-key-here` in `jev_evaluation.py` with your key locally.
Open a terminal in this folder:

```powershell
python jev_evaluation.py
```

The response appears in the terminal and is saved to `response.json`. Failed calls
do not overwrite an existing response, so an old file is not a new assessment.
No CustomerID prompt: edit `request.json` to change the customer data or questions.
The program sends the complete request without dropping fields or calculating answers.
Never put your API key inside the request JSON. Restore the placeholder in the
Python file before committing or sharing it; `.gitignore` does not hide keys in code.

The script reads `request.json`, sends it to JEV, then prints and saves the response.
Errors appear as normal Python exceptions.

## Review the supplied request

The attachment is preserved as supplied, including `model: typesafe/jev-1.14`.
Use a model name available to your direct Typesafe API account if that name is rejected;
the official quickstart uses `jev-latest`.

`identity_status` contains `yes`/`no` fields. The direct API documents optional
`criteria: {"true": "...", "false": "..."}` instead. Its PEP question also differs
from its descriptions about bad records; decide the intended question before editing.
The script sends your request without changing these fields.

References:
- https://docs.typesafe.ai/introduction/quickstart
- https://docs.typesafe.ai/primitives/noul
