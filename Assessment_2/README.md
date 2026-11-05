# On going assessment 2

## II. Access DB2 on Cloud using Python

Executed answers to the ten tasks in the supplied ADY201m brief, section II
(pages 14-20). Reuses the student's Assessment 1 database implementation.

**Saved execution uses the lecturer-approved SQLite alternative documented in
Assessment 1.** IBM Db2 Cloud code is included but has not been executed live.

Open [the executed notebook](02_Access_Database.ipynb) on GitHub, or download
[the HTML report](02_Access_Database.html) to view it in a browser.

| Task | Delivered result |
| --- | --- |
| 1 | Total records |
| 2 | Records with cardiovascular disease |
| 3 | Patient counts by gender code |
| 4 | Ten highest systolic blood pressures; disease count and percentage |
| 5 | Ten heaviest patients above mean weight; disease count and percentage |
| 6 | Ten patients with GLUC > 1; disease count |
| 7 | Ten oldest patients; disease count |
| 8 | Ten patients with CHOLESTEROL = 3; disease count |
| 9 | Ten smokers; disease count |
| 10 | Ten physically active patients; disease count |
| Export | All 70,000 records exported through SQL; every value verified |
| Closure | Original and verification connections closed; database integrity checked |

The notebook includes SQL, tables, findings and a task summary. Sample ordering
is explicit and reproducible; unordered examples in the brief can differ.
Age stays in days. Glucose/cholesterol are category codes. Disease percentages
describe selected samples. Raw outliers are preserved for this database exercise.

### Complete project files

- `02_Access_Database.ipynb`: executed notebook.
- `02_Access_Database.html`: standalone readable report.
- `database_lab.py`: database, query, export and optional Db2 implementation.
- `verify_results.py`: independent calculations from the original CSV.
- `data/`: original CSV, persistent SQLite database, complete SQL export.
- `sql/`: SQLite and Db2 table definitions and queries, including three supplementary queries.
- `results/`: query CSVs, saved results, execution and independent verification evidence.
- `requirements.txt`, `requirements-db2.txt`, `.env.example`: dependencies and empty credential references.

### Run

Use Python 3.12 or a compatible Python environment:

```text
python -m pip install -r requirements.txt
python -m notebook
```

Open `02_Access_Database.ipynb` from this folder and choose **Run All**.
For the database and independent verification without Jupyter:

```text
python database_lab.py
python verify_results.py
```

The verification checks all 13 query answers against independent calculations,
all exported values, database integrity, unique IDs and saved notebook outputs.

### Optional IBM Db2 Cloud

If actual cloud execution is required, load the original semicolon-delimited CSV
into `CARDIO_TRAIN` using `sql/create_table_db2.sql`, install
`requirements-db2.txt`, and use section 7's private credential prompts or the
environment variables in `.env.example`. Set `RUN_DB2 = True` only when ready.
That path uses SSL, executes the queries, exports all records and closes the
connection. Cloud results are stored separately. Never commit credentials.

References: supplied ADY201m brief and dataset;
[sqlite3](https://docs.python.org/3/library/sqlite3.html);
[IBM Db2 Python driver](https://github.com/ibmdb/python-ibmdb).
