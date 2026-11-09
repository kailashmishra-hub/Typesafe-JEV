"""Basic console customer lookup with a JSON export and optional JEV evaluation."""
import json
import os
from pathlib import Path

from customer_lookup import CustomerRepository, DEFAULT_DATA_DIR, normalize_customer_id
from loan_export import build_loan_export

HERE = Path(__file__).resolve().parent


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def main():
    try:
        customer_id = normalize_customer_id(input('Enter CustomerID (example CUST0001): '))
        print('Retrieving customer details...')
        repository = CustomerRepository.load(os.environ.get('CUSTOMER_DATA_DIR', str(DEFAULT_DATA_DIR)))
        customer = build_loan_export(repository.get_customer(customer_id))
        profile = customer['sections']['customer_profile'][0]
        print(f"\nCustomer: {profile['DisplayName']} ({customer_id})")
        for label, field in [('Email', 'Email'), ('City', 'City'), ('Country', 'Country'),
                             ('Status', 'CustomerStatus'), ('Customer since', 'CustomerSince')]:
            print(f'{label}: {profile.get(field) or "Not provided"}')
        period = customer['transaction_period']
        print(f"Transaction period: {period['from']} to {period['to']}")
        print(f"Selected transaction details: {customer['summary']['exported_transaction_count']}")
        print(f"Transactions included in yearly totals: {customer['summary']['transaction_count']}")
        target = HERE / 'exports' / f'{customer_id}_loan_details.json'
        save_json(target, customer)
        print(f'\nCustomer JSON saved to: {target}')
    except (ValueError, OSError, EOFError) as exc:
        print(f'Lookup failed: {exc}')
        return 1

    if not os.environ.get('TYPESAFE_API_KEY', '').strip():
        print('\nJEV evaluation skipped: TYPESAFE_API_KEY is not configured. Customer JSON is ready.')
        return 0
    try:
        consent = input('\nSend this customer JSON to Typesafe JEV for intake evaluation? [y/N]: ')
    except EOFError:
        return 0
    if consent.strip().lower() not in ('y', 'yes'):
        print('Customer lookup complete. JEV evaluation skipped.')
        return 0
    try:
        from jev_evaluation import evaluate_customer
        print('Evaluating with Typesafe JEV...')
        assessment = evaluate_customer(customer)
        result_path = HERE / 'exports' / f'{customer_id}_jev_result.json'
        save_json(result_path, assessment)
        print('\nJEV intake results (not a loan approval):')
        print(json.dumps(assessment, ensure_ascii=False, indent=2))
        print(f'JEV results saved to: {result_path}')
        return 0
    except Exception:
        print('JEV evaluation failed. Check SDK installation, API key, model access and connection. Customer JSON remains saved; no new JEV result was saved.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
