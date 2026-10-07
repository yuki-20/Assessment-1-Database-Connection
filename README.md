# Ongoing Assessment 1 - Part I: Python database connection

[![Verify assessment](https://github.com/yuki-20/Assessment-1-Database-Connection/actions/workflows/verify.yml/badge.svg)](https://github.com/yuki-20/Assessment-1-Database-Connection/actions/workflows/verify.yml)

Open the [executed notebook](01_Database_Connection.ipynb) to read the code and saved results directly on GitHub. Download [the HTML report](01_Database_Connection.html) to view it in a browser.

This submission connects Python to a persistent SQL database, runs the cardiovascular dataset queries, exports the data for offline use, and closes the connection.

**Execution environment: SQLite on the local computer.** The student confirmed that the lecturer permits SQLite instead of IBM Db2 Cloud. The saved notebook results come from SQLite. Optional Db2 SSL connection code is included, but it has not been executed against IBM Cloud.

## Files

| File | Purpose |
| --- | --- |
| `01_Database_Connection.ipynb` | Executed notebook with explanations, SQL, tables and results |
| `01_Database_Connection.html` | Notebook report viewable in a browser after downloading |
| `database_lab.py` | Database creation, cursor queries, export and verification |
| `data/cardio_train_raw.csv` | Original supplied semicolon-delimited dataset |
| `data/cardio_train.sqlite` | Persistent database containing `CARDIO_TRAIN` |
| `data/CARDIO_TRAIN_export.csv` | All records exported through SQL, with no added index column |
| `sql/` | SQLite and optional Db2 table definitions and queries |
| `results/sqlite/` | Query CSVs, summaries and execution evidence |
| `requirements.txt` | Local notebook dependencies |
| `requirements-db2.txt` | Additional driver for the optional Db2 connection |

This repository covers the database portion of the assessment. The later analysis and machine-learning portion is outside this submission's scope.

## Run the assessment

Use Python 3.12. Open a terminal in this repository folder:

```text
python -m pip install -r requirements.txt
python -m notebook
```

Open `01_Database_Connection.ipynb`, select the Python kernel, then choose **Run All**. The default path uses SQLite and does not require an IBM account. Run the notebook from this repository folder so `database_lab.py` can be imported.

For a quick run without Jupyter:

```text
python database_lab.py
```

GitHub Actions automatically runs this database verification and executes every
notebook cell after pushes and pull requests. The workflow is also available from
the repository's **Actions** tab using **Run workflow**. It uses the approved local
SQLite path and requires no IBM credentials.

The first run creates the database and imports the supplied CSV. Later runs compare every database record with the source and reuse the existing table. They do not insert duplicates or replace an existing database that contains different data. Query reports and CSV exports are refreshed on each successful run.

## What the notebook demonstrates

1. Import the Python database libraries and inspect the supplied dataset.
2. Create a persistent SQLite database and connect using `sqlite3.connect`.
3. Query with a cursor, fetch results and display tables.
4. Run the ten API queries from the brief, plus a preview, lowest diastolic blood pressure and alcohol query.
5. Export all records to a CSV for later offline analysis.
6. Close connections and reopen the database in read-only mode to verify persistence and integrity.
7. Show the optional `ibm_db.connect`, `server_info`, `client_info` and `close` workflow for Db2 Cloud.

## Verified results

The exact execution evidence is saved in `results/sqlite/execution_status.json` and in the notebook. The raw CSV contains 70,000 patient records and 13 columns. It includes 34,979 records with `CARDIO = 1` and 35,021 with `CARDIO = 0`.

Age is stored in days. Query Q07 also displays `AGE / 365.0` in years without modifying the source. `GLUC` and `CHOLESTEROL` are category codes, not measurements of consumption. `SMOKE = 1` indicates smoking; it does not record smoking frequency. Ten-record percentages describe only the selected records and are not estimates of a person's clinical risk. Extreme blood pressure values are retained for the raw-data queries and flagged for later cleaning.

Each limited query orders by patient ID to resolve ties. Samples can therefore differ from the unordered examples in the brief. Gender counts are reported by their numeric codes; assigning sex labels requires a confirmed code mapping.

## Optional IBM Db2 Cloud execution

Only use this section if an IBM instance is available and you want actual cloud evidence.

1. Obtain a course-provided Db2 instance or open your own instance in [IBM Cloud](https://cloud.ibm.com/catalog/services/db2).
2. Open the instance's **Service credentials**, create/view a credential, and obtain the database, hostname, SSL port, username and password. [IBM connection instructions](https://cloud.ibm.com/docs/db2-saas?topic=db2-saas-connect_options).
3. Run `sql/create_table_db2.sql` once in a writable schema, then load `data/cardio_train_raw.csv` with delimiter `;` and the header row enabled. Check that 70,000 rows were loaded.
4. Install `requirements-db2.txt`.
5. In the notebook's optional section, set `RUN_DB2 = True` and `ENTER_DB2_CREDENTIALS = True`. Enter the details when prompted; the password prompt hides input. Alternatively, set the environment variables named in `.env.example`. Use `SCHEMA.CARDIO_TRAIN` for `DB2_TABLE` if needed.
6. Run the optional cell. It displays actual server/driver metadata, runs the queries, exports `data/CARDIO_TRAIN_db2_export.csv`, and closes the connection. Optional cloud evidence is stored separately under `results/db2/`.

Do not put passwords in notebook cells or commit a credentials file. The example `.env` values are empty, and `.env.example` is a reference rather than an automatically loaded configuration file.

## Submission link

[yuki-20/Assessment-1-Database-Connection](https://github.com/yuki-20/Assessment-1-Database-Connection)

The repository contains the executed notebook, original dataset, saved SQLite database, SQL files, verified CSV export, query results and an automatic verification workflow. Share the repository link with the lecturer for the database portion of the assessment.

The supplied assignment PDF is intentionally outside this folder because it contains example connection secrets and is not needed to run the submission. This folder contains no copied code or results from another student's repository.

## References

- ADY201m assignment brief and original CSV supplied with this assessment.
- [Python sqlite3 documentation](https://docs.python.org/3/library/sqlite3.html).
- [IBM Db2 Python driver and SSL connection examples](https://github.com/ibmdb/python-ibmdb).
- [IBM Db2 Python API reference](https://github.com/ibmdb/python-ibmdb/wiki/APIs).
