import io
import pandas as pd
from database import get_connection

# Maps known CSV column sets → (table_name, column_mapping)
KNOWN_SCHEMAS = {
    frozenset(["customer_id", "customer_unique_id", "customer_zip_code_prefix", "customer_city", "customer_state"]): (
        "clients",
        {"customer_id": "client_id", "customer_unique_id": "client_unique_id",
         "customer_zip_code_prefix": "code_postal", "customer_city": "ville", "customer_state": "etat"},
    ),
    frozenset(["order_id", "customer_id", "order_status", "order_purchase_timestamp",
               "order_approved_at", "order_delivered_carrier_date",
               "order_delivered_customer_date", "order_estimated_delivery_date"]): (
        "commandes",
        {"order_id": "commande_id", "customer_id": "client_id", "order_status": "statut",
         "order_purchase_timestamp": "date_achat", "order_approved_at": "date_approbation",
         "order_delivered_carrier_date": "date_expedition",
         "order_delivered_customer_date": "date_livraison",
         "order_estimated_delivery_date": "date_livraison_estimee"},
    ),
    frozenset(["product_id", "product_category_name", "product_name_lenght",
               "product_description_lenght", "product_photos_qty", "product_weight_g",
               "product_length_cm", "product_height_cm", "product_width_cm"]): (
        "produits",
        {"product_id": "produit_id", "product_category_name": "categorie",
         "product_name_lenght": "longueur_nom", "product_description_lenght": "longueur_description",
         "product_photos_qty": "nb_photos", "product_weight_g": "poids_g",
         "product_length_cm": "longueur_cm", "product_height_cm": "hauteur_cm",
         "product_width_cm": "largeur_cm"},
    ),
    frozenset(["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"]): (
        "vendeurs",
        {"seller_id": "vendeur_id", "seller_zip_code_prefix": "code_postal",
         "seller_city": "ville", "seller_state": "etat"},
    ),
    frozenset(["order_id", "payment_sequential", "payment_type",
               "payment_installments", "payment_value"]): (
        "paiements",
        {"order_id": "commande_id", "payment_sequential": "sequence",
         "payment_type": "type_paiement", "payment_installments": "nb_versements",
         "payment_value": "montant"},
    ),
    frozenset(["review_id", "order_id", "review_score", "review_comment_title",
               "review_comment_message", "review_creation_date", "review_answer_timestamp"]): (
        "avis",
        {"review_id": "avis_id", "order_id": "commande_id", "review_score": "note",
         "review_comment_title": "titre", "review_comment_message": "commentaire",
         "review_creation_date": "date_creation", "review_answer_timestamp": "date_reponse"},
    ),
}


def _to_python(v):
    if v is None or v is pd.NA:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    if hasattr(v, "item"):
        return v.item()
    return v


def detect_and_import(file_storage):
    """Reads an uploaded CSV, detects the table by columns, cleans and inserts."""
    content = file_storage.read().decode("utf-8", errors="replace")
    df = pd.read_csv(io.StringIO(content))

    # Detect schema by matching column set
    csv_columns = frozenset(df.columns.str.strip())
    matched = None
    for known_cols, (table, mapping) in KNOWN_SCHEMAS.items():
        if known_cols == csv_columns:
            matched = (table, mapping)
            break

    if matched is None:
        raise ValueError(
            f"Colonnes non reconnues : {list(df.columns)}. "
            "Fichier CSV non compatible avec les tables connues."
        )

    table, mapping = matched

    # Clean and map
    df = df.rename(columns=mapping)
    df = df.where(pd.notnull(df), None)

    # Insert
    conn = get_connection()
    cursor = conn.cursor()
    columns = ", ".join(df.columns)
    placeholders = ", ".join(["%s"] * len(df.columns))
    sql = f"INSERT IGNORE INTO {table} ({columns}) VALUES ({placeholders})"
    records = [tuple(_to_python(v) for v in row) for row in df.itertuples(index=False, name=None)]

    total = 0
    for i in range(0, len(records), 500):
        cursor.executemany(sql, records[i:i + 500])
        total += cursor.rowcount

    conn.commit()
    cursor.close()
    conn.close()

    return {"table": table, "lignes": total, "statut": "succes"}


def _serialize(row):
    """Converts datetime objects to ISO strings for JSON serialization."""
    if row is None:
        return None
    return {k: v.isoformat() if hasattr(v, "isoformat") else v for k, v in row.items()}


def get_stats():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            (SELECT COUNT(*) FROM clients)   AS nb_clients,
            (SELECT COUNT(*) FROM commandes) AS nb_commandes,
            (SELECT COUNT(*) FROM produits)  AS nb_produits,
            (SELECT COUNT(*) FROM vendeurs)  AS nb_vendeurs,
            (SELECT COUNT(*) FROM paiements) AS nb_paiements,
            (SELECT COUNT(*) FROM avis)      AS nb_avis
    """)
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


def get_products(limit=100):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT produit_id, categorie, poids_g, longueur_cm, hauteur_cm, largeur_cm
        FROM produits
        LIMIT %s
    """, (limit,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result


def get_orders(limit=100):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT commande_id, client_id, statut, date_achat
        FROM commandes
        LIMIT %s
    """, (limit,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [_serialize(r) for r in rows]


def get_order_detail(order_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT c.commande_id, c.statut, c.date_achat, c.date_livraison,
               c.date_livraison_estimee, cl.ville, cl.etat
        FROM commandes c
        JOIN clients cl ON c.client_id = cl.client_id
        WHERE c.commande_id = %s
    """, (order_id,))
    order = cursor.fetchone()

    if not order:
        cursor.close()
        conn.close()
        return None

    order = _serialize(order)

    cursor.execute("""
        SELECT ac.produit_id, ac.vendeur_id, ac.prix, ac.frais_livraison
        FROM articles_commande ac
        WHERE ac.commande_id = %s
    """, (order_id,))
    order["articles"] = cursor.fetchall()

    cursor.execute("""
        SELECT type_paiement, montant, nb_versements
        FROM paiements
        WHERE commande_id = %s
    """, (order_id,))
    order["paiements"] = cursor.fetchall()

    cursor.execute("""
        SELECT note, titre, commentaire
        FROM avis
        WHERE commande_id = %s
    """, (order_id,))
    order["avis"] = cursor.fetchall()

    cursor.close()
    conn.close()
    return order


def get_revenue_by_state():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT cl.etat,
               ROUND(SUM(p.montant), 2)          AS chiffre_affaires,
               COUNT(DISTINCT c.commande_id)      AS nb_commandes
        FROM commandes c
        JOIN clients cl  ON c.client_id   = cl.client_id
        JOIN paiements p ON c.commande_id = p.commande_id
        GROUP BY cl.etat
        ORDER BY chiffre_affaires DESC
    """)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result


def get_top_categories(limit=10):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT pr.categorie,
               COUNT(*)                  AS nb_ventes,
               ROUND(SUM(ac.prix), 2)   AS revenus_total
        FROM articles_commande ac
        JOIN produits pr ON ac.produit_id = pr.produit_id
        WHERE pr.categorie IS NOT NULL
        GROUP BY pr.categorie
        ORDER BY nb_ventes DESC
        LIMIT %s
    """, (limit,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result
