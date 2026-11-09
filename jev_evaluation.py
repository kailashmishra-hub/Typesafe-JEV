"""Evaluate a loan-intake export with Typesafe; no network call on import."""
import json
import os
from pathlib import Path

from typesafe_sdk import Choice, Noul, TypeSafeClient

QUESTIONS_PATH = Path(__file__).with_name('questions.json')


def load_questions(path=QUESTIONS_PATH):
    definitions = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    constructors = {'choice': Choice, 'noul': Noul}
    questions = {}
    for name, definition in definitions.items():
        fields = dict(definition)
        question_type = fields.pop('type')
        if question_type not in constructors:
            raise ValueError(f'Unsupported question type: {question_type}')
        questions[name] = constructors[question_type](**fields)
    return questions


def evaluate_customer(customer_json, client_factory=TypeSafeClient):
    """Send the same structured state as the download; preserve SDK answers."""
    if not os.environ.get('TYPESAFE_API_KEY', '').strip():
        raise ValueError('Set TYPESAFE_API_KEY in the server environment before evaluating.')
    with client_factory(model=os.environ.get('TYPESAFE_MODEL', 'jev-latest')) as client:
        response = client.system_one(state=customer_json, questions=load_questions())
    return response.model_dump(mode='json')
