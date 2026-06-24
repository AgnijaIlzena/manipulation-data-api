import io
import re
import json
import pandas as pd
from pathlib import Path
from database import get_connection


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sanitize_name(name):
    """Converts any string into a safe MySQL identifier."""
    name = str(name).lower().strip()
    name = re.sub(r"[^a-z0-9_]", "_", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")
    return name[:64]


def infer_sql_type(series):
    """Infers the SQL column type from a pandas Series."""
    if pd.api.types.is_bool_dtype(series):
        return "TINYINT(1)"
    if pd.api.types.is_integer_dtype(series):
        return "BIGINT"
    if pd.api.types.is_float_dtype(series):
        return "FLOAT"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "DATETIME"
    # String column — check max length to choose VARCHAR vs TEXT
    try:
        max_len = int(series.dropna().astype(str).str.len().max())
        if max_len <= 255:
            return f"VARCHAR({max(max_len + 50, 100)})"
    except Exception:
        pass
    return "TEXT"


def clean(df):
    """Replaces NaN/NA with None so MySQL receives NULL."""
    return df.where(pd.notnull(df), None)


def to_python(v):
    """Converts numpy/pandas types to native Python types for MySQL."""
    if v is None or v is pd.NA:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    if hasattr(v, "item"):
        return v.item()
    return v


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def parse_csv(content: str) -> pd.DataFrame:
    """Parses CSV content into a DataFrame, trying common encodings."""
    try:
        return pd.read_csv(io.StringIO(content))
    except Exception:
        return pd.read_csv(io.StringIO(content), encoding="latin-1", sep=None, engine="python")


def parse_json(content: str) -> pd.DataFrame:
    """
    Parses JSON content into a DataFrame.
    Supports: array of objects, or a dict with one list value.
    """
    data = json.loads(content)

    if isinstance(data, list):
        return pd.json_normalize(data)

    if isinstance(data, dict):
        # Find the first key whose value is a list of objects
        for key, val in data.items():
            if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                return pd.json_normalize(val)
        # Single object — wrap in a list
        return pd.json_normalize([data])

    raise ValueError("JSON structure not supported. Expected an array of objects or a dict containing one.")


# ---------------------------------------------------------------------------
# Core: auto-import
# ---------------------------------------------------------------------------

def auto_import(file_storage):
    """
    Reads a CSV or JSON file, infers the schema, creates the table if needed,
    cleans the data and inserts it into MySQL.

    Returns a dict with: table, colonnes, lignes, statut
    """
    filename = file_storage.filename
    extension = Path(filename).suffix.lower()

    if extension not in (".csv", ".json"):
        raise ValueError(f"Type de fichier non supporté : '{extension}'. Seuls .csv et .json sont acceptés.")

    # --- Parse ---
    raw = file_storage.read()
    content = raw.decode("utf-8", errors="replace")

    if extension == ".csv":
        df = parse_csv(content)
    else:
        df = parse_json(content)

    if df.empty:
        raise ValueError("Le fichier est vide ou ne contient aucune ligne.")

    if len(df.columns) == 0:
        raise ValueError("Aucune colonne détectée dans le fichier.")

    # --- Clean column names ---
    df.columns = [sanitize_name(col) for col in df.columns]
    df = df.loc[:, ~df.columns.duplicated()]  # drop duplicate column names

    # --- Derive table name from filename ---
    table_name = sanitize_name(Path(filename).stem)

    # --- Infer SQL types ---
    col_definitions = []
    for col in df.columns:
        sql_type = infer_sql_type(df[col])
        col_definitions.append(f"`{col}` {sql_type}")

    # --- Create table if not exists ---
    create_sql = (
        f"CREATE TABLE IF NOT EXISTS `{table_name}` (\n"
        f"  `_id` INT AUTO_INCREMENT PRIMARY KEY,\n"
        + ",\n  ".join(col_definitions)
        + "\n);"
    )

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(create_sql)
    conn.commit()

    # --- Insert data in chunks ---
    df = clean(df)
    cols = ", ".join(f"`{c}`" for c in df.columns)
    placeholders = ", ".join(["%s"] * len(df.columns))
    insert_sql = f"INSERT INTO `{table_name}` ({cols}) VALUES ({placeholders})"

    records = [
        tuple(to_python(v) for v in row)
        for row in df.itertuples(index=False, name=None)
    ]

    total = 0
    for i in range(0, len(records), 100):
        cursor.executemany(insert_sql, records[i:i + 500])
        total += cursor.rowcount

    conn.commit()
    cursor.close()
    conn.close()

    return {
        "table": table_name,
        "colonnes": list(df.columns),
        "lignes": total,
        "statut": "succes",
    }
