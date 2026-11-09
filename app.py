"""Basic customer profile and a loan-focused JSON download."""
import json
import os
import streamlit as st
from jev_evaluation import evaluate_customer
from customer_lookup import CustomerRepository, DEFAULT_DATA_DIR, normalize_customer_id, source_signature
from loan_export import build_loan_export

st.set_page_config(page_title='Customer Lookup', layout='centered')
st.title('Customer lookup')
st.caption('Find a customer and download their loan application details.')


@st.cache_resource(show_spinner=False)
def load_repository(folder, signature):
    return CustomerRepository.load(folder)


with st.form('customer_search'):
    customer_id = st.text_input('CustomerID', 'CUST0001', placeholder='Enter CustomerID', help='Example: CUST0001')
    submitted = st.form_submit_button('Find customer', type='primary')

if submitted:
    st.session_state.pop('result', None)
    st.session_state.pop('ai_summary', None)
    st.session_state.pop('jev_result', None)
    try:
        customer_id = normalize_customer_id(customer_id)
        folder = os.environ.get('CUSTOMER_DATA_DIR', str(DEFAULT_DATA_DIR))
        signature = source_signature(folder)
        with st.spinner('Finding customer...'):
            repository = load_repository(folder, signature)
            st.session_state['result'] = repository.get_customer(customer_id)
    except Exception as exc:
        st.error(f'Lookup failed: {exc}')

result = st.session_state.get('result')
if result:
    customer = result['sections']['customer_profile'][0]
    st.divider()
    st.subheader(customer['DisplayName'])
    st.caption(f"CustomerID: {result['customer_id']}")
    left, right = st.columns(2)
    with left:
        st.text(f"Email: {customer.get('Email') or 'Not provided'}")
        st.text(f"City: {customer.get('City') or 'Not provided'}")
        st.text(f"Country: {customer.get('Country') or 'Not provided'}")
    with right:
        st.text(f"Status: {customer.get('CustomerStatus') or 'Not provided'}")
        st.text(f"Customer since: {customer.get('CustomerSince') or 'Not provided'}")
    st.divider()
    loan_details = build_loan_export(result)
    st.download_button(
        'Download customer loan details (JSON)',
        json.dumps(loan_details, separators=(',', ':'), ensure_ascii=False, allow_nan=False),
        file_name=f"{result['customer_id']}_loan_details.json",
        mime='application/json',
        type='primary',
    )
    period = loan_details['transaction_period']
    st.caption(f"{period['from']} to {period['to']}: {loan_details['summary']['exported_transaction_count']} selected transaction records. Includes amounts above ₹1,00,000, plus returned payments and AML-linked transactions. Totals cover all {loan_details['summary']['transaction_count']} transactions in that year.")
    st.caption('Evaluate sends this customer export to Typesafe. Demo intake routing only; it does not approve or reject a loan.')
    if st.button('Evaluate with JEV', type='primary'):
        st.session_state.pop('jev_result', None)
        if not os.environ.get('TYPESAFE_API_KEY', '').strip():
            st.warning('Set TYPESAFE_API_KEY in the server environment, then restart the app.')
        else:
            try:
                with st.spinner('Evaluating with Typesafe JEV...'):
                    st.session_state['jev_result'] = evaluate_customer(loan_details)
            except Exception:
                st.error('JEV evaluation failed. Check your API key, model access, connection and account limits, then retry. No result was produced.')
    if st.session_state.get('jev_result') is not None:
        st.subheader('JEV intake assessment')
        st.json(st.session_state['jev_result'])
else:
    st.caption('Demo customers: CUST0001–CUST0050. Synthetic data.')
