import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")

# --- Mapping: CSV English columns → French names for our project ---
COLUMN_MAPS = {
    "olist_customers_dataset.csv": {
        "customer_id": "client_id",
        "customer_unique_id": "client_unique_id",
        "customer_zip_code_prefix": "code_postal",
        "customer_city": "ville",
        "customer_state": "etat",
    },
    "olist_products_dataset.csv": {
        "product_id": "produit_id",
        "product_category_name": "categorie",
        "product_name_lenght": "longueur_nom",
        "product_description_lenght": "longueur_description",
        "product_photos_qty": "nb_photos",
        "product_weight_g": "poids_g",
        "product_length_cm": "longueur_cm",
        "product_height_cm": "hauteur_cm",
        "product_width_cm": "largeur_cm",
    },
    "olist_orders_dataset.csv": {
        "order_id": "commande_id",
        "customer_id": "client_id",
        "order_status": "statut",
        "order_purchase_timestamp": "date_achat",
        "order_approved_at": "date_approbation",
        "order_delivered_carrier_date": "date_expedition",
        "order_delivered_customer_date": "date_livraison",
        "order_estimated_delivery_date": "date_livraison_estimee",
    },
    "olist_sellers_dataset.csv": {
        "seller_id": "vendeur_id",
        "seller_zip_code_prefix": "code_postal",
        "seller_city": "ville",
        "seller_state": "etat",
    },
    "olist_order_payments_dataset.csv": {
        "order_id": "commande_id",
        "payment_sequential": "sequence",
        "payment_type": "type_paiement",
        "payment_installments": "nb_versements",
        "payment_value": "montant",
    },
    "olist_order_reviews_dataset.csv": {
        "review_id": "avis_id",
        "order_id": "commande_id",
        "review_score": "note",
        "review_comment_title": "titre",
        "review_comment_message": "commentaire",
        "review_creation_date": "date_creation",
        "review_answer_timestamp": "date_reponse",
    },
}

# --- Load and display each dataset ---
for filename, column_map in COLUMN_MAPS.items():
    file_path = DATA_DIR / filename
    df = pd.read_csv(file_path)
    df = df.rename(columns=column_map)

    label = filename.replace("olist_", "").replace("_dataset.csv", "").upper()
    print(f"\n{'='*50}")
    print(f" {label}")
    print(f"{'='*50}")
    print(f"Lignes : {len(df):,}  |  Colonnes : {list(df.columns)}")
    print(df.head(3).to_string())
