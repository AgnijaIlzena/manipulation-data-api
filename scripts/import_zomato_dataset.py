import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from database import get_connection

DATA_DIR = Path(__file__).parent.parent / "data" / "zomato"

# =============================================================================
# MAPPING: colonnes CSV source → colonnes SQL cible
# =============================================================================

MAPPING_RESTAURANTS = {
    "Restaurant ID":        "restaurant_id",
    "Restaurant Name":      "nom",
    "Country Code":         "code_pays",
    "City":                 "ville",
    "Address":              "adresse",
    "Locality":             "localite",
    "Locality Verbose":     "localite_complete",
    "Longitude":            "longitude",
    "Latitude":             "latitude",
    "Cuisines":             "cuisines",
    "Average Cost for two": "cout_moyen_deux",
    "Currency":             "devise",
    "Has Table booking":    "reservation_table",    # Yes/No → 1/0
    "Has Online delivery":  "livraison_en_ligne",   # Yes/No → 1/0
    "Is delivering now":    "livre_maintenant",     # Yes/No → 1/0
    "Switch to order menu": "commande_en_ligne",    # Yes/No → 1/0
    "Price range":          "gamme_prix",
    "Aggregate rating":     "note",
    "Rating color":         "couleur_note",
    "Rating text":          "texte_note",
    "Votes":                "votes",
}

MAPPING_PAYS = {
    "Country Code": "code_pays",
    "Country":      "nom_pays",
}


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def read_csv(filename):
    """Lit un fichier CSV depuis data/zomato/ (encodage latin-1 pour Zomato)."""
    return pd.read_csv(DATA_DIR / filename, encoding="latin-1")


def read_excel(filename):
    """Lit un fichier Excel depuis data/zomato/."""
    return pd.read_excel(DATA_DIR / filename)


def convert_empty_values(df):
    """Convertit les valeurs vides (NaN) en None pour que MySQL reçoive NULL."""
    return df.where(pd.notnull(df), None)


def convert_yes_no(df, columns):
    """Convertit Yes/No en 1/0 pour les colonnes booléennes."""
    for col in columns:
        if col in df.columns:
            df[col] = df[col].map({"Yes": 1, "No": 0})
    return df


def to_python(v):
    """Convertit les types numpy/pandas en types Python natifs pour MySQL."""
    if v is None or v is pd.NA:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    if hasattr(v, "item"):
        return v.item()
    return v


def bulk_insert(cursor, table, df, chunk_size=500):
    """Insère en masse un DataFrame dans une table MySQL par petits lots."""
    if df.empty:
        return
    columns = ", ".join(df.columns)
    placeholders = ", ".join(["%s"] * len(df.columns))
    sql = f"INSERT IGNORE INTO {table} ({columns}) VALUES ({placeholders})"
    records = [
        tuple(to_python(v) for v in row)
        for row in df.itertuples(index=False, name=None)
    ]
    total = 0
    for i in range(0, len(records), chunk_size):
        chunk = records[i: i + chunk_size]
        cursor.executemany(sql, chunk)
        total += cursor.rowcount
    print(f"  {table}: {total} lignes inserees")


# =============================================================================
# IMPORT PAR TABLE
# =============================================================================

def import_pays(cursor):
    """Importe les pays depuis Country-Code.xlsx."""
    df = read_excel("Country-Code.xlsx")
    df = df.rename(columns=MAPPING_PAYS)
    df = df[["code_pays", "nom_pays"]].drop_duplicates(subset="code_pays")
    bulk_insert(cursor, "pays", convert_empty_values(df))


def import_restaurants(cursor):
    """Importe les restaurants depuis zomato.csv."""
    df = read_csv("zomato.csv")
    df = df.rename(columns=MAPPING_RESTAURANTS)

    bool_cols = ["reservation_table", "livraison_en_ligne", "livre_maintenant", "commande_en_ligne"]
    df = convert_yes_no(df, bool_cols)

    bulk_insert(cursor, "restaurants", convert_empty_values(df))


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

def import_all():
    conn = get_connection()
    cursor = conn.cursor()

    steps = [
        ("pays",         import_pays),
        ("restaurants",  import_restaurants),
    ]

    for label, fn in steps:
        print(f"Importation {label}...")
        fn(cursor)
        conn.commit()

    cursor.close()
    conn.close()
    print("\nImportation Zomato terminee.")


if __name__ == "__main__":
    import_all()
