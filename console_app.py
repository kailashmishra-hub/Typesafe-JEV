import json
from pathlib import Path
from openpyxl import load_workbook

folder = Path(__file__).resolve().parent
data_folder = folder / 'data'
customer_id = input('Enter CustomerID: ').strip()

sections = {}

for file in sorted(data_folder.glob('*.xlsx')):
    workbook = load_workbook(file, read_only=True, data_only=True)
    for sheet in workbook:
        rows = sheet.iter_rows(values_only=True)
        columns = next(rows, ())
        if 'CustomerID' in columns:
            customer_column = columns.index('CustomerID')
            # Match only CustomerID; retain every transaction type, amount and date.
            sections.setdefault(sheet.title, []).extend(
                dict(zip(columns, row)) for row in rows
                if row[customer_column] == customer_id
            )
    workbook.close()

if not sections.get('Customers'):
    print('Customer not found.')
else:
    result = {'sections': sections}
    output = json.dumps(result, indent=2, ensure_ascii=False, default=str)
    exports = folder / 'exports'
    exports.mkdir(exist_ok=True)
    output_file = exports / f'{customer_id}_loan_details.json'
    output_file.write_text(output, encoding='utf-8')

    print(json.dumps(sections['Customers'], indent=2, ensure_ascii=False, default=str))
    for section, records in sections.items():
        print(f'{section}: {len(records)} records exported')
    print(f'All customer records saved to: {output_file}')
