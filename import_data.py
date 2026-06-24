import pandas as pd
from pathlib import Path
from database import get_connection

DATA_DIR = Path("data")


def clean(df):
    """Replace NaN with None so MySQL receives NULL."""
    return df.where(pd.notnull(df), None)


def bulk_insert(cursor, table, df):
    if df.empty:
        return
    columns = ", ".join(df.columns)
    placeholders = ", ".join(["%s"] * len(df.columns))
    sql = f"INSERT IGNORE INTO {table} ({columns}) VALUES ({placeholders})"
    records = [tuple(row) for row in df.itertuples(index=False, name=None)]
    cursor.executemany(sql, records)
    print(f"  {table}: {cursor.rowcount} lignes inserees")


def import_all():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. clients
    print("Importation clients...")
    df = pd.read_csv(DATA_DIR / "olist_customers_dataset.csv")
    df = df.rename(columns={
        "customer_id": "client_id",
        "customer_unique_id": "client_unique_id",
        "customer_zip_code_prefix": "code_postal",
        "customer_city": "ville",
        "customer_state": "etat",
    })
    bulk_insert(cursor, "clients", clean(df))
    conn.commit()

    # 2. vendeurs
    print("Importation vendeurs...")
    df = pd.read_csv(DATA_DIR / "olist_sellers_dataset.csv")
    df = df.rename(columns={
        "seller_id": "vendeur_id",
        "seller_zip_code_prefix": "code_postal",
        "seller_city": "ville",
        "seller_state": "etat",
    })
    bulk_insert(cursor, "vendeurs", clean(df))
    conn.commit()

    # 3. produits
    print("Importation produits...")
    df = pd.read_csv(DATA_DIR / "olist_products_dataset.csv")
    df = df.rename(columns={
        "product_id": "produit_id",
        "product_category_name": "categorie",
        "product_name_lenght": "longueur_nom",
        "product_description_lenght": "longueur_description",
        "product_photos_qty": "nb_photos",
        "product_weight_g": "poids_g",
        "product_length_cm": "longueur_cm",
        "product_height_cm": "hauteur_cm",
        "product_width_cm": "largeur_cm",
    })
    for col in ["longueur_nom", "longueur_description", "nb_photos"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    bulk_insert(cursor, "produits", clean(df))
    conn.commit()

    # 4. commandes (depends on clients)
    print("Importation commandes...")
    df = pd.read_csv(DATA_DIR / "olist_orders_dataset.csv")
    df = df.rename(columns={
        "order_id": "commande_id",
        "customer_id": "client_id",
        "order_status": "statut",
        "order_purchase_timestamp": "date_achat",
        "order_approved_at": "date_approbation",
        "order_delivered_carrier_date": "date_expedition",
        "order_delivered_customer_date": "date_livraison",
        "order_estimated_delivery_date": "date_livraison_estimee",
    })
    bulk_insert(cursor, "commandes", clean(df))
    conn.commit()

    # 5. articles_commande (depends on commandes, produits, vendeurs)
    print("Importation articles_commande...")
    df = pd.read_csv(DATA_DIR / "olist_order_items_dataset.csv")
    df = df.rename(columns={
        "order_id": "commande_id",
        "order_item_id": "numero_article",
        "product_id": "produit_id",
        "seller_id": "vendeur_id",
        "shipping_limit_date": "date_limite_expedition",
        "price": "prix",
        "freight_value": "frais_livraison",
    })
    bulk_insert(cursor, "articles_commande", clean(df))
    conn.commit()

    # 6. paiements (depends on commandes)
    print("Importation paiements...")
    df = pd.read_csv(DATA_DIR / "olist_order_payments_dataset.csv")
    df = df.rename(columns={
        "order_id": "commande_id",
        "payment_sequential": "sequence",
        "payment_type": "type_paiement",
        "payment_installments": "nb_versements",
        "payment_value": "montant",
    })
    bulk_insert(cursor, "paiements", clean(df))
    conn.commit()

    # 7. avis (depends on commandes) — drop_duplicates on avis_id
    print("Importation avis...")
    df = pd.read_csv(DATA_DIR / "olist_order_reviews_dataset.csv")
    df = df.rename(columns={
        "review_id": "avis_id",
        "order_id": "commande_id",
        "review_score": "note",
        "review_comment_title": "titre",
        "review_comment_message": "commentaire",
        "review_creation_date": "date_creation",
        "review_answer_timestamp": "date_reponse",
    })
    df = df.drop_duplicates(subset="avis_id")
    bulk_insert(cursor, "avis", clean(df))
    conn.commit()

    cursor.close()
    conn.close()
    print("\nImportation terminee.")


if __name__ == "__main__":
    import_all()
