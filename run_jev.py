import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from dotenv import load_dotenv

folder = Path(__file__).resolve().parent
load_dotenv(folder / ".env")

customer = json.loads(
    (folder / "exports/CUST0002_loan_details.json").read_text(encoding="utf-8-sig")
)
questions = json.loads(
    (folder / "questions.json").read_text(encoding="utf-8-sig")
)

payload = {
    "model": "jev-latest",
    "state": customer,
    "questions": questions,
}

request = Request(
    "https://api.typesafe.ai/v1/systemone",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {os.environ['TYPESAFE_API_KEY']}",
        "Content-Type": "application/json",
    },
    method="POST",
)

try:
    with urlopen(request, timeout=180) as response:
        result = json.load(response)
except HTTPError as error:
    print(error.read().decode("utf-8"))
    raise SystemExit(1)

output = json.dumps(result, indent=2, ensure_ascii=False)
print(output)
(folder / "response.json").write_text(output, encoding="utf-8")