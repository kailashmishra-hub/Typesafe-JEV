import copy
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from customer_lookup import CustomerRepository
from loan_export import build_loan_export
from jev_evaluation import evaluate_customer, load_questions
from typesafe_sdk import Choice, Noul


class JevIntegrationTests(unittest.TestCase):
    def test_question_contract(self):
        questions = load_questions()
        self.assertIsInstance(questions['documents_verified'], Noul)
        self.assertIsInstance(questions['compliance_review_required'], Noul)
        self.assertIsInstance(questions['next_workflow_action'], Choice)

    def test_missing_key_does_not_call_api(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, 'TYPESAFE_API_KEY'):
                evaluate_customer({}, client_factory=lambda **kwargs: self.fail('API called'))

    def test_state_and_response_preserved(self):
        state = {'customer_id': 'CUST0001', 'sections': {'transactions': []}}
        original = copy.deepcopy(state)
        captured = {}
        expected = {'answers': {'documents_verified': {'type': 'noul', 'noul': 0.93}}}

        class FakeResponse:
            def model_dump(self, mode):
                return expected

        class FakeClient:
            def __init__(self, **kwargs):
                captured.update(kwargs)
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def system_one(self, **kwargs):
                captured.update(kwargs)
                return FakeResponse()

        with patch.dict(os.environ, {'TYPESAFE_API_KEY': 'test-placeholder', 'TYPESAFE_MODEL': 'jev-latest'}):
            result = evaluate_customer(state, client_factory=FakeClient)
        self.assertEqual(result, expected)
        self.assertEqual(state, original)
        self.assertIs(captured['state'], state)
        self.assertEqual(captured['model'], 'jev-latest')
        self.assertEqual(len(captured['questions']), 3)

    def test_customer_export(self):
        repository = CustomerRepository.load()
        customer = repository.get_customer('CUST0001')
        result = build_loan_export(customer)
        self.assertEqual(len(repository.customer_ids()), 50)
        self.assertEqual(result['summary']['transaction_count'], 120)
        self.assertEqual(len(result['sections']['transactions']), 12)
        self.assertTrue(all(t['TransactionAmountINR'] > 100000 for t in result['sections']['transactions']))


if __name__ == '__main__':
    unittest.main()
