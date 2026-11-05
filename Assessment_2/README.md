# Assessment 2: Database Access with Python

Section II of the ADY201m brief: retrieve patient records through Python, answer
ten SQL questions, export the table and close the connection.

Open the [executed notebook](02_Access_Database.ipynb), or download the
[HTML report](02_Access_Database.html). Results use the approved SQLite database
alternative. Optional Db2 SSL code is included in the notebook.

| Task | Query |
| --- | --- |
| 1 | Count all patient records |
| 2 | Count cardiovascular disease cases |
| 3 | Count patients by gender code |
| 4 | Select the ten highest systolic pressures; calculate disease percentage |
| 5 | Select ten patients above mean weight; calculate disease percentage |
| 6 | Select ten patients with glucose category above normal; count disease cases |
| 7 | Select the ten oldest patients; count disease cases |
| 8 | Select ten patients with cholesterol category 3; count disease cases |
| 9 | Select ten smokers; count disease cases |
| 10 | Select ten physically active patients; count disease cases |

The export contains all 70,000 records and 13 original columns. Every exported
value is checked against the source. Both database connections are closed, and
the persisted database passes its integrity check.

Samples use explicit ordering with ID to resolve ties. Task 5 selects the ten
heaviest patients above the mean. Unordered examples in the brief can return
different samples. Age stays in days; disease percentages describe the selected
records. Numeric category codes retain their supplied meaning.

## Files and execution

The folder includes the original dataset, SQLite database, SQL export, notebook,
HTML report, database helper, SQLite/Db2 SQL and per-query results. Q11-Q13 are
supplementary exercises retained from the shared database implementation.

With Python 3.12, run from this folder:

```text
python -m pip install -r requirements.txt
python -m notebook
```

Choose **Run All** in the notebook. To verify every query and the complete export:

```text
python verify_results.py
```

For Db2, install `requirements-db2.txt`, load the source CSV into `CARDIO_TRAIN`
and use the notebook's private credential prompts. Live cloud execution is not
included in the saved results.
