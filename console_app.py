import json
from pathlib import Path

folder = Path(__file__).resolve().parent
data_folder = folder / 'data'
customer_id = input('Enter CustomerID: ').strip()

customers = json.loads((data_folder / 'customers.json').read_text(encoding='utf-8-sig'))
customer = next((row for row in customers if row['CustomerID'] == customer_id), None)

if customer is None:
    print('Customer not found.')
else:
    sections = {'customer_profile': [row for row in customers if row['CustomerID'] == customer_id]}

    for file in sorted(data_folder.glob('*.json')):
        if file.name != 'customers.json':
            records = json.loads(file.read_text(encoding='utf-8-sig'))
            sections[file.stem] = [row for row in records if row['CustomerID'] == customer_id]

    result = {'sections': sections}
    output = json.dumps(result, indent=2, ensure_ascii=False)
    exports = folder / 'exports'
    exports.mkdir(exist_ok=True)
    output_file = exports / f'{customer_id}_loan_details.json'
    output_file.write_text(output, encoding='utf-8')

    print(json.dumps(customer, indent=2, ensure_ascii=False))
    print(f'All customer records saved to: {output_file}')
