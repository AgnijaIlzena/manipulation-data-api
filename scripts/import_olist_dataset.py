import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from database import get_connection

DATA_DIR = Path(__file__).parent.parent / "data"

# =============================================================================
# MAPPING: colonnes CSV source → colonnes SQL cible
# =============================================================================

MAPPING_CLIENTS = {
    "customer_id":              "client_id",         # Texte conservé (PK)
    "customer_unique_id":       "client_unique_id",  # Texte conservé
    "customer_zip_code_prefix": "code_postal",       # Texte nettoyé
    "customer_city":            "ville",             # Texte nettoyé (minuscules)
    "customer_state":           "etat",              # Texte nettoyé
}

MAPPING_VENDEURS = {
    "seller_id":                "vendeur_id",        # Texte conservé (PK)
    "seller_zip_code_prefix":   "code_postal",       # Texte nettoyé
    "seller_city":              "ville",             # Texte nettoyé
    "seller_state":             "etat",              # Texte nettoyé
}

MAPPING_PRODUITS = {
    "product_id":               "produit_id",        # Texte conservé (PK)
    "product_category_name":    "categorie",         # Texte nettoyé
    "product_name_lenght":      "longueur_nom",      # Conversion int
    "product_description_lenght": "longueur_description",  # Conversion int
    "product_photos_qty":       "nb_photos",         # Conversion int
    "product_weight_g":         "poids_g",           # Conversion float
    "product_length_cm":        "longueur_cm",       # Conversion float
    "product_height_cm":        "hauteur_cm",        # Conversion float
    "product_width_cm":         "largeur_cm",        # Conversion float
}

MAPPING_COMMANDES = {
    "order_id":                      "commande_id",           # Texte conservé (PK)
    "customer_id":                   "client_id",             # FK → clients
    "order_status":                  "statut",                # Texte nettoyé
    "order_purchase_timestamp":      "date_achat",            # Conversion date
    "order_approved_at":             "date_approbation",      # Conversion date
    "order_delivered_carrier_date":  "date_expedition",       # Conversion date
    "order_delivered_customer_date": "date_livraison",        # Conversion date
    "order_estimated_delivery_date": "date_livraison_estimee",# Conversion date
}

MAPPING_ARTICLES = {
    "order_id":           "commande_id",           # FK → commandes
    "order_item_id":      "numero_article",        # Conversion int (PK partielle)
    "product_id":         "produit_id",            # FK → produits
    "seller_id":          "vendeur_id",            # FK → vendeurs
    "shipping_limit_date":"date_limite_expedition",# Conversion date
    "price":              "prix",                  # Conversion float
    "freight_value":      "frais_livraison",       # Conversion float
}

MAPPING_PAIEMENTS = {
    "order_id":             "commande_id",   # FK → commandes
    "payment_sequential":   "sequence",      # Conversion int (PK partielle)
    "payment_type":         "type_paiement", # Texte nettoyé
    "payment_installments": "nb_versements", # Conversion int
    "payment_value":        "montant",       # Conversion float
}

MAPPING_AVIS = {
    "review_id":              "avis_id",        # Texte conservé (PK)
    "order_id":               "commande_id",    # FK → commandes
    "review_score":           "note",           # Conversion int
    "review_comment_title":   "titre",          # Texte nettoyé
    "review_comment_message": "commentaire",    # Texte nettoyé
    "review_creation_date":   "date_creation",  # Conversion date
    "review_answer_timestamp":"date_reponse",   # Conversion date
}


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def read_csv(filename):
    """Lit un fichier CSV depuis le dossier data/ et retourne un DataFrame."""
    return pd.read_csv(DATA_DIR / filename)


def convert_empty_values(df):
    """Convertit les valeurs vides (NaN) en None pour que MySQL reçoive NULL."""
    return df.where(pd.notnull(df), None)


def to_python(v):
    """Convertit les types numpy/pandas en types Python natifs pour MySQL."""
    if v is None or v is pd.NA:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    if hasattr(v, "item"):  # numpy.int64, numpy.float64, etc.
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
# IMPORT PAR TABLE (ordre FK : parents avant enfants)
# =============================================================================

def import_clients(cursor):
    df = read_csv("olist_customers_dataset.csv")
    df = df.rename(columns=MAPPING_CLIENTS)
    bulk_insert(cursor, "clients", convert_empty_values(df))


def import_vendeurs(cursor):
    df = read_csv("olist_sellers_dataset.csv")
    df = df.rename(columns=MAPPING_VENDEURS)
    bulk_insert(cursor, "vendeurs", convert_empty_values(df))


def import_produits(cursor):
    df = read_csv("olist_products_dataset.csv")
    df = df.rename(columns=MAPPING_PRODUITS)
    for col in ["longueur_nom", "longueur_description", "nb_photos"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    bulk_insert(cursor, "produits", convert_empty_values(df))


def import_commandes(cursor):
    df = read_csv("olist_orders_dataset.csv")
    df = df.rename(columns=MAPPING_COMMANDES)
    bulk_insert(cursor, "commandes", convert_empty_values(df))


def import_articles_commande(cursor):
    df = read_csv("olist_order_items_dataset.csv")
    df = df.rename(columns=MAPPING_ARTICLES)
    bulk_insert(cursor, "articles_commande", convert_empty_values(df))


def import_paiements(cursor):
    df = read_csv("olist_order_payments_dataset.csv")
    df = df.rename(columns=MAPPING_PAIEMENTS)
    bulk_insert(cursor, "paiements", convert_empty_values(df))


def import_avis(cursor):
    df = read_csv("olist_order_reviews_dataset.csv")
    df = df.rename(columns=MAPPING_AVIS)
    df = df.drop_duplicates(subset="avis_id")
    bulk_insert(cursor, "avis", convert_empty_values(df))


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

def import_all():
    conn = get_connection()
    cursor = conn.cursor()

    steps = [
        ("clients",           import_clients),
        ("vendeurs",          import_vendeurs),
        ("produits",          import_produits),
        ("commandes",         import_commandes),
        ("articles_commande", import_articles_commande),
        ("paiements",         import_paiements),
        ("avis",              import_avis),
    ]

    for label, fn in steps:
        print(f"Importation {label}...")
        fn(cursor)
        conn.commit()

    cursor.close()
    conn.close()
    print("\nImportation terminee.")


if __name__ == "__main__":
    import_all()
