"""Verify all three local assessment deliverables without retraining models."""
from pathlib import Path
import json
import subprocess
import sys

import nbformat

ROOT = Path(__file__).resolve().parent


def verify():
    subprocess.run([sys.executable, 'database_lab.py'], cwd=ROOT, check=True)
    for folder in ('Assessment_2', 'Assessment_3'):
        subprocess.run([sys.executable, 'verify_results.py'], cwd=ROOT / folder, check=True)
    notebooks = ['01_Database_Connection.ipynb', 'Assessment_2/02_Access_Database.ipynb',
                 'Assessment_3/03_Data_Analysis.ipynb']
    counts = {}
    for name in notebooks:
        notebook = nbformat.read(ROOT / name, as_version=4)
        nbformat.validate(notebook)
        cells = [c for c in notebook.cells if c.cell_type == 'code']
        assert [c.execution_count for c in cells] == list(range(1, len(cells) + 1)), name
        assert all(o.output_type != 'error' for c in cells for o in c.outputs), name
        assert (ROOT / name).with_suffix('.html').is_file(), name
        counts[name] = len(cells)
    report = {'local_verification_passed': True, 'notebook_code_cells': counts,
              'source_records': 70000, 'cloud_executed': False}
    (ROOT / 'results/verification_summary.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('PASS: all three local assessments; every notebook has saved, error-free output.')


if __name__ == '__main__':
    verify()
