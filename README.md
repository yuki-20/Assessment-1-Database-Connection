# ADY201m Assessment 1: Database Connection with Python

Connect Python to a persistent SQL database, retrieve patient records, export
the complete table and close the connection.

Open the [executed notebook](01_Database_Connection.ipynb), or download the
[HTML report](01_Database_Connection.html).

## Separate assessment repositories

- [Assessment 2: Access the Database with Python](https://github.com/yuki-20/Assessment-2-Database-Access)
- [Assessment 3: Data Analysis with Python](https://github.com/yuki-20/Assessment-3-Data-Analysis)

Each repository includes its own notebook, report, input data and verification
code. They can be downloaded and run independently.

## Results

The database contains 70,000 records and 13 original columns. All values match
the supplied CSV. The full SQL export is verified against the source, the
database passes its integrity check, and both connections are closed.

The table contains 34,979 disease cases and 35,021 records without disease.
Age remains in days. Raw measurements are preserved in the database and export.

## Run

Use Python 3.12. From this repository folder:

```text
python -m pip install -r requirements.txt
python -m notebook
```

Open `01_Database_Connection.ipynb`, select the Python kernel and choose
**Run All**. To run the database verification without Jupyter:

```text
python database_lab.py
```

| Location | Contents |
| --- | --- |
| `01_Database_Connection.ipynb` | Executed connection notebook |
| `01_Database_Connection.html` | Standalone report |
| `database_lab.py` | Connection, queries, export and verification |
| `data/` | Original CSV, SQLite database and complete SQL export |
| `sql/` | SQLite and IBM Db2 table definitions and queries |
| `results/` | Database results and execution records |

## Environment

Saved results use the previously approved SQLite alternative to IBM Db2 Cloud.
The notebook also includes optional SSL Db2 code. To run that path, install
`requirements-db2.txt` and use private service credentials through the prompts
or environment variables in `.env.example`. Live cloud execution is not
included in the saved results.

The supplied brief is excluded because it contains example connection secrets.
The original dataset is included.

## References

- Supplied ADY201m assignment brief, section I, and cardiovascular dataset.
- [Python sqlite3](https://docs.python.org/3/library/sqlite3.html).
- [IBM Db2 Python driver](https://github.com/ibmdb/python-ibmdb).
