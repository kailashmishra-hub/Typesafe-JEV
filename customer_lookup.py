"""Retrieve complete customer records from the eight supplied Excel workbooks."""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
import json
from pathlib import Path
import re
from zipfile import BadZipFile

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

HERE = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = HERE / 'data' if (HERE / 'data').is_dir() else HERE.parent / 'loan_customer_data_expanded'

# section, workbook, worksheet, unique row key
SOURCES = (
    ('customer_profile', '01_Customers.xlsx', 'Customers', ('CustomerID',)),
    ('employment_income', '02_Employment_Income.xlsx', 'EmploymentIncome', ('CustomerID',)),
    ('loan_applications', '03_Loan_Applications.xlsx', 'Applications', ('ApplicationID',)),
    ('existing_liabilities', '04_Existing_Liabilities.xlsx', 'Liabilities', ('LiabilityID',)),
    ('banking_monthly', '05_Banking_Summaries.xlsx', 'BankingMonthly', ('AccountID', 'StatementMonth')),
    ('application_documents', '06_Application_Documents.xlsx', 'Documents', ('DocumentID',)),
    ('credit_history', '07_Credit_History.xlsx', 'CreditHistory', ('CustomerID',)),
    ('accounts', '08_History_and_Compliance.xlsx', 'Accounts', ('AccountID',)),
    ('transactions', '08_History_and_Compliance.xlsx', 'Transactions', ('TransactionID',)),
    ('kyc_history', '08_History_and_Compliance.xlsx', 'KYCHistory', ('KYCReviewID',)),
    ('screening_history', '08_History_and_Compliance.xlsx', 'ScreeningHistory', ('ScreeningID',)),
    ('aml_cases', '08_History_and_Compliance.xlsx', 'AMLCaseHistory', ('AMLCaseID',)),
    ('funds_and_wealth', '08_History_and_Compliance.xlsx', 'FundsAndWealth', ('DeclarationID',)),
)


class DataError(ValueError):
    """A required source is missing, invalid, or inconsistent."""


def normalize_customer_id(value: str) -> str:
    value = value.strip().upper()
    if not re.fullmatch(r'CUST\d{4}', value):
        raise ValueError('Enter a CustomerID such as CUST0001.')
    return value


def _value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()[:10]
    return value


def source_signature(folder: str | Path) -> tuple:
    """Used by the UI to reload when any source workbook changes."""
    folder = Path(folder).expanduser().resolve()
    signature = []
    for filename in sorted({source[1] for source in SOURCES}):
        path = folder / filename
        try:
            stat = path.stat()
        except FileNotFoundError as exc:
            raise DataError(f'Missing workbook: {path}') from exc
        signature.append((filename, stat.st_mtime_ns, stat.st_size))
    return tuple(signature)


def _read_sheet(book, filename, sheet_name, keys):
    if sheet_name not in book.sheetnames:
        raise DataError(f'Missing sheet {sheet_name!r} in {filename}.')
    iterator = book[sheet_name].iter_rows(values_only=False)
    header_row = next(iterator, ())
    headers = [cell.value for cell in header_row]
    if not headers or any(not isinstance(h, str) or not h.strip() for h in headers) or len(set(headers)) != len(headers):
        raise DataError(f'Invalid headers in {filename}/{sheet_name}.')
    if not {'CustomerID', *keys}.issubset(headers):
        raise DataError(f'Missing CustomerID or primary-key column in {filename}/{sheet_name}.')
    seen, rows = set(), []
    for cells in iterator:
        if all(cell.value is None for cell in cells):
            continue
        if any(cell.data_type in {'e', 'f'} for cell in cells):
            raise DataError(f'Excel error or formula in {filename}/{sheet_name}, row {cells[0].row}. Supply literal source values.')
        row = dict(zip(headers, (_value(cell.value) for cell in cells)))
        if not isinstance(row['CustomerID'], str) or row['CustomerID'] != normalize_customer_id(row['CustomerID']):
            raise DataError(f'Invalid source CustomerID in {filename}/{sheet_name}.')
        key = tuple(row[k] for k in keys)
        if any(k is None or k == '' for k in key) or key in seen:
            raise DataError(f'Missing or duplicate row key {key} in {filename}/{sheet_name}.')
        seen.add(key)
        rows.append(row)
    return rows


@dataclass
class CustomerRepository:
    folder: Path
    records: dict
    by_customer: dict

    @classmethod
    def load(cls, folder: str | Path = DEFAULT_DATA_DIR) -> 'CustomerRepository':
        folder = Path(folder).expanduser().resolve()
        before = source_signature(folder)
        records = {}
        # Open each workbook once; the history file contains six customer tables.
        for filename in sorted({s[1] for s in SOURCES}):
            try:
                book = load_workbook(folder / filename, read_only=True, data_only=False)
                try:
                    for section, file, sheet, keys in SOURCES:
                        if file == filename:
                            records[section] = _read_sheet(book, file, sheet, keys)
                finally:
                    book.close()
            except (OSError, KeyError, BadZipFile, InvalidFileException) as exc:
                raise DataError(f'Cannot read {filename}: {exc}') from exc
        if before != source_signature(folder):
            raise DataError('An Excel file changed while loading. Retry after saving and closing the workbooks.')
        index = {}
        for section, rows in records.items():
            grouped = defaultdict(list)
            for row in rows:
                grouped[row['CustomerID']].append(row)
            index[section] = dict(grouped)
        repo = cls(folder, records, index)
        repo._validate_links()
        return repo

    def _validate_links(self):
        customers = set(self.by_customer['customer_profile'])
        if not customers:
            raise DataError('Customer master is empty.')
        for section, grouped in self.by_customer.items():
            if not set(grouped).issubset(customers):
                raise DataError(f'Unknown CustomerID in {section}.')
        for section in ('employment_income', 'credit_history'):
            if set(self.by_customer[section]) != customers:
                raise DataError(f'Missing customer coverage in {section}.')
        for section in ('accounts', 'banking_monthly', 'transactions', 'loan_applications', 'application_documents', 'kyc_history', 'screening_history', 'funds_and_wealth'):
            if set(self.by_customer[section]) != customers:
                raise DataError(f'Missing customer coverage in {section} for this complete demo dataset.')
        maps = {section: {r[key]: r['CustomerID'] for r in self.records[section]} for section, key in (
            ('accounts', 'AccountID'), ('loan_applications', 'ApplicationID'),
            ('transactions', 'TransactionID'), ('screening_history', 'ScreeningID'), ('aml_cases', 'AMLCaseID'))}
        for section, field, target, optional in (
            ('banking_monthly', 'AccountID', 'accounts', False),
            ('transactions', 'AccountID', 'accounts', False),
            ('application_documents', 'ApplicationID', 'loan_applications', False),
            ('aml_cases', 'TriggerTransactionID', 'transactions', True),
            ('aml_cases', 'RelatedScreeningID', 'screening_history', True),
            ('screening_history', 'CaseReference', 'aml_cases', True),
        ):
            for row in self.records[section]:
                key = row.get(field)
                if key is None and optional:
                    continue
                if maps[target].get(key) != row['CustomerID']:
                    raise DataError(f'Broken {field} link in {section}: {key!r}.')

    def customer_ids(self) -> list[str]:
        return sorted(self.by_customer['customer_profile'])

    def get_customer(self, customer_id: str) -> dict:
        customer_id = normalize_customer_id(customer_id)
        if customer_id not in self.by_customer['customer_profile']:
            raise ValueError(f'Customer not found: {customer_id}. Demo IDs are CUST0001–CUST0050.')
        # A JSON round trip returns an independent, serializable result; no caller can mutate the cache.
        sections = json.loads(json.dumps({section: self.by_customer[section].get(customer_id, []) for section, *_ in SOURCES}))
        transactions = sections['transactions']
        withdrawals = [r for r in transactions if r['TransactionType'] == 'cash_withdrawal' and r['PostingStatus'] == 'posted']
        latest_kyc = max(sections['kyc_history'], key=lambda r: (r['ReviewStartedOn'], r['KYCReviewID']), default=None)
        completed = [r for r in sections['kyc_history'] if r['ReviewStatus'] == 'completed' and r['CompletedOn']]
        last_completed = max(completed, key=lambda r: r['CompletedOn'], default=None)
        latest_screening = {}
        for row in sorted(sections['screening_history'], key=lambda r: (r['ScreeningDate'], r['ScreeningID'])):
            latest_screening[row['ScreeningCategory']] = row
        dates = [r['TransactionDate'] for r in transactions]
        return {
            'customer_id': customer_id,
            'summary': {
                'display_name': sections['customer_profile'][0]['DisplayName'],
                'account_count': len(sections['accounts']),
                'transaction_count': len(transactions),
                'history_start': min(dates) if dates else None,
                'history_end': max(dates) if dates else None,
                'cash_withdrawal_count': len(withdrawals),
                'cash_withdrawal_total_inr': sum(r['TransactionAmountINR'] for r in withdrawals),
                'latest_kyc_review': latest_kyc,
                'last_completed_kyc': last_completed,
                'latest_screening_by_category': latest_screening,
                'open_aml_case_count': sum(r['CaseStatus'] != 'closed' for r in sections['aml_cases']),
            },
            'record_counts': {section: len(rows) for section, rows in sections.items()},
            'sections': sections,
            'provenance': {
                'synthetic': True,
                'data_as_of': sections['customer_profile'][0]['DataAsOf'],
                'sources': {section: {'workbook': file, 'sheet': sheet} for section, file, sheet, _ in SOURCES},
                'excluded_sheets': ['Guide', 'FieldDictionary'],
                'note': 'Guide and FieldDictionary describe the dataset; they are not customer records. Screening matches and investigation outcomes are preserved separately.',
            },
        }


def get_customer_details(customer_id: str, data_dir: str | Path = DEFAULT_DATA_DIR) -> dict:
    """Convenience API. For repeated requests, load CustomerRepository once instead."""
    return CustomerRepository.load(data_dir).get_customer(customer_id)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('customer_id', nargs='?', help='Example: CUST0001. Omit to type it interactively.')
    parser.add_argument('--data-dir', type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument('--output', type=Path, help='JSON output path. Defaults to exports/<CustomerID>.json.')
    parser.add_argument('--json', action='store_true', help='Write the complete JSON to stdout instead of a file.')
    args = parser.parse_args()
    try:
        entered = args.customer_id or input('Enter CustomerID (e.g. CUST0001): ')
        customer_id = normalize_customer_id(entered)
        result = get_customer_details(customer_id, args.data_dir)
        text = json.dumps(result, indent=2)
        if args.json:
            print(text)
        else:
            target = args.output or HERE / 'exports' / f'{customer_id}.json'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding='utf-8')
            print(f"{customer_id}: {result['summary']['display_name']}")
            for section, count in result['record_counts'].items():
                print(f'  {section}: {count} record(s)')
            print(f'Complete details saved to: {target.resolve()}')
    except (ValueError, OSError, EOFError) as exc:
        parser.exit(1, f'Lookup failed: {exc}\n')


if __name__ == '__main__':
    main()
