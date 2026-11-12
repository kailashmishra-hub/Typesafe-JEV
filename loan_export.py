"""Loan export with yearly activity totals and selected transaction details."""
from copy import deepcopy
from datetime import date, timedelta
from calendar import monthrange
from decimal import Decimal

# Remove metadata, not amounts, events, outcomes, or meaningful review notes.
OMIT = {
    'customer_profile': {'PreferredContact'},
    'loan_applications': {'CustomerQuery'},
    'banking_monthly': {'BankName'},  # Bank is retained once in accounts.
    'accounts': {'AccountRelationship', 'StatementCoverage'},
    'kyc_history': {'KYCReviewID', 'ReviewerID', 'EvidenceReference', 'IdentityEvidenceType', 'AddressEvidenceType'},
    'screening_history': {'ListProvider', 'ListSnapshotDate', 'ReviewerID'},
    'aml_cases': {'ReviewerID'},
    'funds_and_wealth': {'ReviewerID', 'EvidenceReference'},
}

# These exact strings are generated boilerplate in this synthetic dataset.
# A different or meaningful narrative is retained unchanged.
BOILERPLATE = {
    ('transactions', 'Description'): {
        'Income received', 'Other incoming funds', 'Cash withdrawal',
        'Payment returned without settlement',
    },
    ('application_documents', 'ReviewNote'): {'Evidence verified in this synthetic scenario.'},
    ('kyc_history', 'ReviewNotes'): {
        'Historical onboarding review at the loan institution.',
        'Previous periodic review.', 'Current periodic review completed.',
    },
    ('screening_history', 'Notes'): {'No match in simulated screening.'},
}


def build_loan_export(customer):
    """The raw repository result is unchanged; this is a separate export view."""
    sections = customer['sections']
    profile = sections['customer_profile'][0]
    as_of = profile.get('DataAsOf')
    # Use complete statement months available by the snapshot, not today's date.
    last_complete = date.fromisoformat(as_of).replace(day=1) - timedelta(days=1)
    available_months = [date.fromisoformat(r['StatementMonth']) for r in sections['banking_monthly'] if date.fromisoformat(r['StatementMonth']) <= last_complete.replace(day=1)]
    last_month = max(available_months, default=last_complete.replace(day=1))
    month_index = last_month.year * 12 + last_month.month - 1 - 11
    start = date(month_index // 12, month_index % 12 + 1, 1).isoformat()
    end = date(last_month.year, last_month.month, monthrange(last_month.year,last_month.month)[1]).isoformat()
    recent_transactions = [r for r in sections['transactions'] if start <= r['TransactionDate'] <= end]
    if any(r.get('Currency') != 'INR' for r in recent_transactions):
        raise ValueError('The INR transaction filter requires INR source amounts; foreign-currency values need conversion before applying the threshold.')
    aml_transaction_ids = {r['TriggerTransactionID'] for r in sections['aml_cases'] if r.get('TriggerTransactionID')}
    included_transactions = []
    for row in recent_transactions:
        reasons = []
        amount = Decimal(str(row['TransactionAmountINR']))
        if not amount.is_finite() or amount < 0:
            raise ValueError('Invalid transaction amount in source data.')
        if amount > Decimal('100000'):
            reasons.append('amount_above_100000_inr')
        if row['PostingStatus'] == 'returned':
            reasons.append('returned_payment')
        if row['TransactionID'] in aml_transaction_ids:
            reasons.append('aml_linked')
        if reasons:
            included_transactions.append({**row, 'SelectionReasons':reasons})
    sections = {**sections, 'transactions':included_transactions}
    currencies = {row['Currency'] for rows in sections.values() for row in rows if row.get('Currency')}
    shared_currency = next(iter(currencies)) if len(currencies) == 1 else None
    selected = {}
    for section, rows in sections.items():
        selected_rows = []
        for row in rows:
            if row.get('CustomerID') != customer['customer_id']:
                raise ValueError('Cannot export rows belonging to another customer.')
            trimmed = {}
            for key, value in row.items():
                if key == 'CustomerID' or key in OMIT.get(section, set()):
                    continue
                if key == 'DataAsOf' and value == as_of:
                    continue
                if key == 'Currency' and shared_currency is not None and value == shared_currency:
                    continue
                if isinstance(value, str) and value in BOILERPLATE.get((section, key), set()):
                    continue
                trimmed[key] = deepcopy(value)
            selected_rows.append(trimmed)
        if section == 'banking_monthly':
            # Write long history field names once. Every retained cell remains typed.
            columns = list(dict.fromkeys(k for row in selected_rows for k in row))
            selected[section] = {'columns': columns, 'rows': [[row.get(k) for k in columns] for row in selected_rows]}
        else:
            selected[section] = selected_rows
    # Recompute this small summary from the authoritative history, not duplicated summaries.
    completed = [r for r in sections['kyc_history'] if r.get('ReviewStatus') == 'completed' and r.get('CompletedOn')]
    last = max(completed, key=lambda r:r['CompletedOn'], default=None)
    summary = {k:deepcopy(v) for k,v in customer['summary'].items() if k not in {
        'display_name', 'latest_kyc_review', 'last_completed_kyc', 'latest_screening_by_category'
    }}
    summary['last_completed_kyc'] = {
        'completed_on': last['CompletedOn'] if last else None,
        'status': last['ReviewStatus'] if last else 'not_completed',
    }
    withdrawals = [r for r in recent_transactions if r['TransactionType']=='cash_withdrawal' and r['PostingStatus']=='posted']
    dates = [r['TransactionDate'] for r in recent_transactions]
    summary.update(transaction_count=len(recent_transactions), history_start=min(dates,default=None), history_end=max(dates,default=None), cash_withdrawal_count=len(withdrawals), cash_withdrawal_total_inr=float(sum((Decimal(str(r['TransactionAmountINR'])) for r in withdrawals),Decimal(0))))
    def total(rows):
        return float(sum((Decimal(str(r['TransactionAmountINR'])) for r in rows),Decimal(0)))
    posted = [r for r in recent_transactions if r['PostingStatus']=='posted']
    returned = [r for r in recent_transactions if r['PostingStatus']=='returned']
    summary['transaction_activity'] = {
        'basis':'all_transactions_in_transaction_period_before_detail_filter',
        'total_transaction_count':len(recent_transactions),
        'posted_transaction_count':len(posted),
        'posted_credits_inr':total([r for r in posted if r['Direction']=='credit']),
        'posted_debits_inr':total([r for r in posted if r['Direction']=='debit']),
        'income_credits_inr':total([r for r in posted if r['TransactionType']=='income_credit']),
        'cash_withdrawal_count':len(withdrawals),
        'cash_withdrawals_inr':total(withdrawals),
        'repayment_count':sum(r['TransactionType']=='repayment' for r in posted),
        'repayments_inr':total([r for r in posted if r['TransactionType']=='repayment']),
        'returned_payment_count':len(returned),
        'returned_attempted_amount_inr':total(returned),
    }
    summary['exported_transaction_count'] = len(included_transactions)
    result = {'customer_id':customer['customer_id'], 'as_of':as_of, 'transaction_period':{'from':start,'to':end}}
    result['transaction_selection'] = {
        'amount_greater_than_inr':100000,
        'include_returned_payments_regardless_of_amount':True,
        'include_aml_linked_transactions_regardless_of_amount':True,
        'applies_within_transaction_period':True,
        'included_count':len(included_transactions),
        'excluded_count':len(recent_transactions)-len(included_transactions),
    }
    if shared_currency:
        result['currency'] = shared_currency
    result.update(summary=summary, sections=selected)
    return result
