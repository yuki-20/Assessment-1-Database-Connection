# ADY201m: Cardiovascular Data Analysis

Three assessments covering Python database connections, SQL data retrieval and
classification of cardiovascular disease using 70,000 patient records.

| Assessment | Notebook | Report | Scope |
| --- | --- | --- | --- |
| 1. Connect to a database using Python | [Notebook](01_Database_Connection.ipynb) | [HTML](01_Database_Connection.html) | Connection, metadata, retrieval, export and closure |
| 2. Access the database using Python | [Notebook](Assessment_2/02_Access_Database.ipynb) | [HTML](Assessment_2/02_Access_Database.html) | Ten SQL exercises, patient samples and disease proportions |
| 3. Data Analysis with Python | [Notebook](Assessment_3/03_Data_Analysis.ipynb) | [HTML](Assessment_3/03_Data_Analysis.html) | Exploration, cleaning, hypothesis tests, OLS and classification |

Notebooks include executed code and results. Download an HTML report to read it
in a browser without Jupyter.

## Results

- The database and complete SQL export match all 70,000 original records.
- Assessment 2 includes all ten required queries, plus three supplementary queries.
- Assessment 3 compares seven classifiers and three additional tuning settings.
- The selected gradient-boosting model achieves **73.20% test accuracy** and
  **0.799 ROC AUC** on 21,000 held-out records. Its 95% accuracy interval is
  72.60%-73.80%; the majority-class baseline is 50.03%.

Model selection uses a separate validation partition. Blood-pressure clipping,
scaling and category encoding are fitted within the training pipelines.
The model is an academic analysis of this dataset, not a diagnostic tool.

## Run locally

Use Python 3.12. From the repository folder:

```text
python -m pip install -r requirements.txt
python -m notebook
```

Open a notebook from its containing folder, select the Python kernel and choose
**Run All**. Assessment 3 reads `data/CARDIO_TRAIN_export.csv` from the repository
root; keep the downloaded project structure intact.

Check the data, SQL results, saved analysis and notebook outputs:

```text
python verify_all.py
```

This verification does not retrain the classifiers. Running the Assessment 3
notebook reproduces the complete analysis and training process.

## Project structure

| Location | Contents |
| --- | --- |
| Root notebook and `database_lab.py` | Assessment 1 and shared database implementation |
| `data/` | Original CSV, persistent SQLite database and full SQL export |
| `sql/` | Table definitions and queries for SQLite and IBM Db2 |
| `results/` | Database results and execution records |
| `Assessment_2/` | Assessment 2 notebook, report and standalone project files |
| `Assessment_3/` | Analysis code, notebook, report, figures, tests and model results |
| `requirements.txt` | Versions used to execute the local notebooks |

## Execution environment

The database assessments use the previously approved SQLite alternative to IBM
Db2 Cloud. Optional SSL Db2 code is included in the database notebooks; install
`requirements-db2.txt` and supply private credentials through the prompts or
environment variables in `.env.example` to run it.

All published results were generated locally. IBM Db2 Cloud and Watson Studio
were not executed. The brief's Watson Studio rerun remains outstanding unless
the lecturer approves a local substitute.

The supplied brief is excluded because it contains example connection secrets.
The original dataset and reproducible project files are included.

## References

- Supplied ADY201m assignment brief and cardiovascular dataset.
- [Dataset description](https://www.kaggle.com/datasets/sulianova/cardiovascular-disease-dataset).
- [Python sqlite3](https://docs.python.org/3/library/sqlite3.html).
- [IBM Db2 Python driver](https://github.com/ibmdb/python-ibmdb).
- [scikit-learn](https://scikit-learn.org/stable/), [SciPy](https://docs.scipy.org/doc/scipy/reference/stats.html), [statsmodels](https://www.statsmodels.org/stable/).
