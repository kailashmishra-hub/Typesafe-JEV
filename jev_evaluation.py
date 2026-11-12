import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

os.environ['TYPESAFE_API_KEY'] = 'your-typesafe-key-here'  # Replace with your key locally.

folder = Path(__file__).resolve().parent
payload = json.loads((folder / 'request.json').read_text(encoding='utf-8-sig'))

request = Request(
    'https://api.typesafe.ai/v1/systemone',
    data=json.dumps(payload).encode('utf-8'),
    headers={
        'Authorization': f"Bearer {os.environ['TYPESAFE_API_KEY']}",
        'Content-Type': 'application/json',
    },
    method='POST',
)

with urlopen(request, timeout=180) as response:
    result = json.load(response)

output = json.dumps(result, indent=2, ensure_ascii=False)
print(output)
(folder / 'response.json').write_text(output, encoding='utf-8')
