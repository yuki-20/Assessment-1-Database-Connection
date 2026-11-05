"""Run with Python: compare SQL answers and the full export against raw CSV data."""
from collections import Counter
from pathlib import Path
import csv
import json
import math
import sqlite3

from database_lab import COLUMNS, ROOT, run_sqlite_lab


def verify():
    results, status = run_sqlite_lab()
    with (ROOT / 'data/cardio_train_raw.csv').open(encoding='utf-8-sig', newline='') as stream:
        records = [{k.upper(): float(v) if k == 'weight' else int(v)
                    for k, v in row.items()} for row in csv.DictReader(stream, delimiter=';')]
    assert len(records) == 70000
    assert len({r['ID'] for r in records}) == len(records)
    expected = {
        'Q01': [(len(records),)],
        'Q02': [(sum(r['CARDIO'] == 1 for r in records),)],
        'Q03': sorted(Counter(r['GENDER'] for r in records).items()),
    }
    mean_weight = sum(r['WEIGHT'] for r in records) / len(records)
    selections = {
        'Q04': sorted(records, key=lambda r: (-r['AP_HI'], r['ID']))[:10],
        'Q05': sorted((r for r in records if r['WEIGHT'] > mean_weight),
                      key=lambda r: (-r['WEIGHT'], r['ID']))[:10],
        'Q06': sorted((r for r in records if r['GLUC'] > 1), key=lambda r: r['ID'])[:10],
        'Q07': sorted(records, key=lambda r: (-r['AGE'], r['ID']))[:10],
        'Q08': sorted((r for r in records if r['CHOLESTEROL'] == 3), key=lambda r: r['ID'])[:10],
        'Q09': sorted((r for r in records if r['SMOKE'] == 1), key=lambda r: r['ID'])[:10],
        'Q10': sorted((r for r in records if r['ACTIVE'] == 1), key=lambda r: r['ID'])[:10],
        'Q11': sorted(records, key=lambda r: r['ID'])[:10],
        'Q12': sorted(records, key=lambda r: (r['AP_LO'], r['ID']))[:10],
        'Q13': sorted((r for r in records if r['ALCO'] == 1), key=lambda r: r['ID'])[:10],
    }
    assert [r['id'] for r in results] == [f'Q{i:02}' for i in range(1, 14)]
    for result in results:
        qid = result['id']
        if qid in selections:
            selected = selections[qid]
            answer = [tuple(r['AGE'] / 365.0 if col == 'AGE_YEARS' else r[col]
                            for col in result['columns']) for r in selected]
            assert result['sample_size'] == 10
            assert result['disease_cases'] == sum(r['CARDIO'] for r in selected)
            assert math.isclose(result['disease_percent'], 10 * sum(r['CARDIO'] for r in selected))
        else:
            answer = expected[qid]
        assert result['rows'] == answer, qid
        with (ROOT / f'results/sqlite/{qid}.csv').open(newline='') as stream:
            output = list(csv.reader(stream))
        assert output[0] == result['columns']
        assert output[1:] == [[str(v) for v in row] for row in answer], qid
    with (ROOT / 'data/CARDIO_TRAIN_export.csv').open(newline='') as stream:
        reader = csv.DictReader(stream)
        assert tuple(reader.fieldnames) == COLUMNS
        exported = [{k: float(v) if k == 'WEIGHT' else int(v) for k, v in r.items()} for r in reader]
    assert exported == sorted(records, key=lambda r: r['ID'])
    connection = sqlite3.connect((ROOT / 'data/cardio_train.sqlite').as_uri() + '?mode=ro', uri=True)
    try:
        assert connection.execute('PRAGMA integrity_check').fetchone() == ('ok',)
        assert connection.execute('SELECT COUNT(*), COUNT(DISTINCT ID) FROM CARDIO_TRAIN').fetchone() == (70000, 70000)
    finally:
        connection.close()
    assert status['success'] and status['connection_closed'] and status['reopened_connection_closed']
    saved = json.loads((ROOT / '02_Access_Database.ipynb').read_text(encoding='utf-8'))
    cells = [c for c in saved['cells'] if c['cell_type'] == 'code']
    assert [c['execution_count'] for c in cells] == list(range(1, len(cells) + 1))
    assert not any(o['output_type'] == 'error' for c in cells for o in c['outputs'])
    report = {'success': True, 'required_tasks_verified': 10, 'supplementary_queries_verified': 3,
              'source_records': len(records), 'export_all_records_match': True,
              'saved_notebook_code_cells': len(cells), 'cloud_executed': False}
    (ROOT / 'results/independent_verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    verify()
