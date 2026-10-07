"""Part I database lab: approved local execution and optional IBM Db2 execution."""

from pathlib import Path
import csv
import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parent
RAW_CSV = ROOT / "data" / "cardio_train_raw.csv"
COLUMNS = (
    "ID", "AGE", "GENDER", "HEIGHT", "WEIGHT", "AP_HI", "AP_LO",
    "CHOLESTEROL", "GLUC", "SMOKE", "ALCO", "ACTIVE", "CARDIO",
)


def source_records():
    """Preserve original units, including age in days and all outliers."""
    with RAW_CSV.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter=";")
        if tuple(name.upper() for name in reader.fieldnames) != COLUMNS:
            raise ValueError("The input CSV columns do not match the assignment.")
        records = [tuple(float(row[name.lower()]) if name == "WEIGHT"
                         else int(row[name.lower()]) for name in COLUMNS)
                   for row in reader]
    if len({row[0] for row in records}) != len(records):
        raise ValueError("The CSV contains duplicate patient IDs.")
    return sorted(records, key=lambda row: row[0])


def query_specs(engine="sqlite", table="CARDIO_TRAIN"):
    """Use ID to resolve ties and make every ten-record selection repeatable."""
    if engine not in ("sqlite", "db2"):
        raise ValueError("Choose sqlite or db2.")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?", table):
        raise ValueError("Use an ordinary TABLE or SCHEMA.TABLE identifier.")
    limit = " LIMIT 10" if engine == "sqlite" else " FETCH FIRST 10 ROWS ONLY"
    definitions = [
        ("Q01", "Total patient records", f"SELECT COUNT(*) AS TOTAL_ROWS FROM {table}"),
        ("Q02", "Records with cardiovascular disease", f"SELECT COUNT(*) AS DISEASE_CASES FROM {table} WHERE CARDIO = 1"),
        ("Q03", "Patient counts by gender code", f"SELECT GENDER, COUNT(*) AS PATIENTS FROM {table} GROUP BY GENDER ORDER BY GENDER"),
        ("Q04", "Ten highest systolic blood pressure values", f"SELECT ID, AP_HI, CARDIO FROM {table} ORDER BY AP_HI DESC, ID" + limit),
        ("Q05", "Ten heaviest patients above the average weight", f"SELECT ID, WEIGHT, CARDIO FROM {table} WHERE WEIGHT > (SELECT AVG(WEIGHT) FROM {table}) ORDER BY WEIGHT DESC, ID" + limit),
        ("Q06", "Ten patients with glucose above normal", f"SELECT ID, GLUC, CARDIO FROM {table} WHERE GLUC > 1 ORDER BY ID" + limit),
        ("Q07", "Ten oldest patients (age in days)", f"SELECT ID, AGE, AGE / 365.0 AS AGE_YEARS, CARDIO FROM {table} ORDER BY AGE DESC, ID" + limit),
        ("Q08", "Ten patients with cholesterol code 3", f"SELECT ID, CHOLESTEROL, CARDIO FROM {table} WHERE CHOLESTEROL = 3 ORDER BY ID" + limit),
        ("Q09", "Ten patients who smoke", f"SELECT ID, SMOKE, CARDIO FROM {table} WHERE SMOKE = 1 ORDER BY ID" + limit),
        ("Q10", "Ten physically active patients", f"SELECT ID, ACTIVE, CARDIO FROM {table} WHERE ACTIVE = 1 ORDER BY ID" + limit),
        ("Q11", "Preview ten patient records", f"SELECT * FROM {table} ORDER BY ID" + limit),
        ("Q12", "Ten lowest diastolic blood pressure values", f"SELECT ID, AP_LO, CARDIO FROM {table} ORDER BY AP_LO, ID" + limit),
        ("Q13", "Ten patients who drink alcohol", f"SELECT ID, ALCO, CARDIO FROM {table} WHERE ALCO = 1 ORDER BY ID" + limit),
    ]
    return definitions


def fetch_result(connection, sql):
    """Execute a SELECT using a DB-API cursor and release its resources."""
    cursor = connection.cursor()
    try:
        cursor.execute(sql)
        headers = [item[0].upper() for item in cursor.description]
        rows = [tuple(row) for row in cursor.fetchall()]
        return headers, rows
    finally:
        cursor.close()


def write_csv(path, headers, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(rows)


def collect_queries(connection, engine, table, output_dir):
    results = []
    for query_id, title, sql in query_specs(engine, table):
        headers, rows = fetch_result(connection, sql)
        result = {"id": query_id, "title": title, "sql": sql,
                  "columns": headers, "rows": rows}
        if "CARDIO" in headers:
            index = headers.index("CARDIO")
            cases = sum(int(row[index]) == 1 for row in rows)
            result.update(disease_cases=cases, sample_size=len(rows),
                          disease_percent=100 * cases / len(rows) if rows else None)
        write_csv(output_dir / f"{query_id}.csv", headers, rows)
        results.append(result)
    (output_dir / "query_results.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8")
    return results


def run_sqlite_lab():
    """Create once, verify the complete table on reruns, query, export and close."""
    records = source_records()
    database_path = ROOT / "data" / "cardio_train.sqlite"
    output_dir = ROOT / "results" / "sqlite"
    output_dir.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    status = {"engine": "SQLite", "cloud_executed": False,
              "lecturer_approved_local_alternative": True,
              "source_sha256": hashlib.sha256(RAW_CSV.read_bytes()).hexdigest(),
              "executed_at_utc": datetime.now(timezone.utc).isoformat()}
    try:
        exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='CARDIO_TRAIN'"
        ).fetchone()
        if not exists:
            with connection:
                connection.executescript((ROOT / "sql" / "create_table_sqlite.sql").read_text())
                connection.executemany(
                    "INSERT INTO CARDIO_TRAIN VALUES (" + ",".join("?" for _ in COLUMNS) + ")",
                    records,
                )
        headers, stored = fetch_result(connection, "SELECT * FROM CARDIO_TRAIN ORDER BY ID")
        if tuple(headers) != COLUMNS or stored != records:
            raise ValueError("The saved database differs from the source CSV; it was not overwritten.")
        status["all_source_records_match"] = True
        status["row_count"] = len(stored)
        status["disease_cases"] = sum(row[-1] for row in stored)
        results = collect_queries(connection, "sqlite", "CARDIO_TRAIN", output_dir)
        export_path = ROOT / "data" / "CARDIO_TRAIN_export.csv"
        write_csv(export_path, headers, stored)
    finally:
        connection.close()
    # Verify the database remains usable after the original connection closes.
    reopened = sqlite3.connect(database_path.as_uri() + "?mode=ro", uri=True)
    try:
        status["integrity_check"] = reopened.execute("PRAGMA integrity_check").fetchone()[0]
        count, cases = reopened.execute("SELECT COUNT(*), SUM(CARDIO) FROM CARDIO_TRAIN").fetchone()
        if (count, cases) != (len(records), sum(row[-1] for row in records)):
            raise ValueError("The reopened database counts differ from the source.")
    finally:
        reopened.close()
    # Re-read every exported value, rather than checking only the row count.
    with export_path.open(encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream)
        if tuple(next(reader)) != COLUMNS:
            raise ValueError("Unexpected export headers.")
        exported = [tuple(float(value) if name == "WEIGHT" else int(value)
                          for name, value in zip(COLUMNS, row, strict=True)) for row in reader]
    if exported != records or status["integrity_check"] != "ok":
        raise ValueError("Database integrity or CSV verification failed.")
    status.update(connection_closed=True, reopened_connection_closed=True,
                  export_matches_source=True, executed_queries=len(results),
                  export_rows=len(exported), success=True)
    (output_dir / "execution_status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    return results, status


def run_db2_lab():
    """Optional live Db2 path; no example credentials and no fabricated cloud output."""
    import ibm_db
    import ibm_db_dbi

    keys = {"DATABASE": "DB2_DATABASE", "HOSTNAME": "DB2_HOSTNAME", "PORT": "DB2_PORT",
            "UID": "DB2_UID", "PWD": "DB2_PWD"}
    values = {key: os.environ.get(env, "") for key, env in keys.items()}
    missing = [keys[key] for key, value in values.items() if not value]
    if missing:
        raise ValueError("Set these environment variables first: " + ", ".join(missing))
    if not values["PORT"].isdigit() or not 1 <= int(values["PORT"]) <= 65535:
        raise ValueError("DB2_PORT must be the SSL port supplied by IBM.")
    # These values use the standard simple IBM service-credential format.
    # Reject separators rather than silently corrupting an ODBC connection string.
    if any(any(char in value for char in ";\r\n") for value in values.values()):
        raise ValueError("Connection values containing separators require a configured driver DSN.")
    table = os.environ.get("DB2_TABLE", "CARDIO_TRAIN")
    query_specs("db2", table)  # Validate identifier before establishing a connection.
    dsn = "DRIVER={IBM DB2 ODBC DRIVER};" + "".join(f"{key}={value};" for key, value in values.items())
    dsn += "PROTOCOL=TCPIP;SECURITY=SSL;CONNECTTIMEOUT=20;"
    cert = os.environ.get("DB2_SSL_CERT", "")
    if cert:
        cert_path = Path(cert).expanduser().resolve()
        if not cert_path.is_file() or ";" in str(cert_path):
            raise ValueError("DB2_SSL_CERT must point to an existing certificate file.")
        dsn += f"SSLServerCertificate={cert_path};"
    connection = None
    output_dir = ROOT / "results" / "db2"
    output_dir.mkdir(parents=True, exist_ok=True)
    status = {"engine": "IBM Db2", "cloud_executed": False, "success": False,
              "executed_at_utc": datetime.now(timezone.utc).isoformat()}
    try:
        connection = ibm_db.connect(dsn, "", "")
        if not connection:
            raise RuntimeError("Db2 did not return a connection.")
        print("Connected to Db2 Cloud over SSL.")
        server = ibm_db.server_info(connection)
        client = ibm_db.client_info(connection)
        status["server"] = {name: getattr(server, name) for name in ("DBMS_NAME", "DBMS_VER", "DB_NAME")}
        status["driver"] = {name: getattr(client, name) for name in (
            "DRIVER_NAME", "DRIVER_VER", "DATA_SOURCE_NAME", "DRIVER_ODBC_VER",
            "ODBC_VER", "ODBC_SQL_CONFORMANCE", "APPL_CODEPAGE", "CONN_CODEPAGE")}
        print("Server metadata:", status["server"])
        print("Driver metadata:", status["driver"])
        dbapi_connection = ibm_db_dbi.Connection(connection)
        results = collect_queries(dbapi_connection, "db2", table, output_dir)
        headers, rows = fetch_result(dbapi_connection, f"SELECT * FROM {table} ORDER BY ID")
        write_csv(ROOT / "data" / "CARDIO_TRAIN_db2_export.csv", headers, rows)
        status.update(cloud_executed=True, success=True, executed_queries=len(results), export_rows=len(rows))
    except Exception:
        # Do not print the DSN, password or raw driver exception into a public notebook.
        state = ibm_db.conn_error(connection) if connection else ibm_db.conn_error()
        status["sqlstate"] = state
        raise RuntimeError("Db2 execution failed. Check credentials, SSL endpoint, table/schema and permissions. SQLSTATE: " + str(state)) from None
    finally:
        if connection:
            status["connection_closed"] = bool(ibm_db.close(connection))
            print("Db2 connection closed:", status["connection_closed"])
        else:
            status["connection_closed"] = True
        (output_dir / "execution_status.json").write_text(json.dumps(status, indent=2, default=str), encoding="utf-8")
    return results, status


if __name__ == "__main__":
    _, execution_status = run_sqlite_lab()
    print(json.dumps(execution_status, indent=2))
