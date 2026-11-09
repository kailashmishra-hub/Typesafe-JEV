"""Send request.json to Typesafe JEV using Python's standard library."""
import argparse
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

HERE = Path(__file__).resolve().parent
ENDPOINT = 'https://api.typesafe.ai/v1/systemone'


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f'Invalid JSON number: {value}')


def load_request(path):
    body = Path(path).read_bytes()
    payload = json.loads(body.decode('utf-8-sig'), object_pairs_hook=unique_keys,
                         parse_constant=reject_constant)
    if not isinstance(payload, dict) or not isinstance(payload.get('model'), str) or not payload['model'].strip():
        raise ValueError('Request must contain a nonempty model name.')
    if 'state' not in payload or not isinstance(payload.get('questions'), dict) or not payload['questions']:
        raise ValueError('Request must contain state and a nonempty questions object.')
    # Strip only an optional UTF-8 BOM, retaining all supplied JSON fields/values.
    return body.removeprefix(b'\xef\xbb\xbf'), payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('request', nargs='?', type=Path, default=HERE / 'request.json')
    parser.add_argument('--dry-run', action='store_true', help='Check local JSON only; no API call.')
    args = parser.parse_args()
    try:
        body, payload = load_request(args.request)
        print(f"Model: {payload['model']}; questions: {len(payload['questions'])}; request bytes: {len(body):,}")
        for name, question in payload['questions'].items():
            if isinstance(question, dict) and question.get('type') == 'noul' and ('yes' in question or 'no' in question):
                print(f'Note: {name} uses yes/no fields; the direct API documents criteria.true/criteria.false. Review this question before sending. No fields were changed.')
        if args.dry_run:
            print('JSON checked locally. No model/schema validation or API call performed.')
            return 0
        api_key = os.environ.get('TYPESAFE_API_KEY', '').strip()
        if not api_key:
            print('Set TYPESAFE_API_KEY in your terminal, then run again.')
            return 1
        request = urllib.request.Request(
            ENDPOINT, data=body, method='POST',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json',
                     'Accept': 'application/json'},
        )
        print('Sending request to Typesafe JEV...')
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.load(response)
        text = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
        output = HERE / 'response.json'
        output.write_text(text, encoding='utf-8')
        print(text)
        print(f'\nResponse saved to: {output}')
        return 0
    except urllib.error.HTTPError as exc:
        print(f'Typesafe returned HTTP {exc.code}. Check the API key, model name, question schema, request limits and account access. No new response was saved.')
        return 1
    except (OSError, ValueError) as exc:
        print(f'Request failed ({type(exc).__name__}). Check the input JSON, file access and connection. No new response was saved.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
