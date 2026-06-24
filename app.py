import os
from dotenv import load_dotenv
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from flask import Flask
from flask_cors import CORS
from flask_restx import Api, Resource, fields

from olist_repository import (
    get_stats,
    get_products,
    get_orders,
    get_order_detail,
    get_revenue_by_state,
    get_top_categories,
)

load_dotenv()

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[FlaskIntegration()],
    send_default_pii=True,
    traces_sample_rate=1.0,
    release=os.getenv("SENTRY_RELEASE", "dev"),
    environment=os.getenv("SENTRY_ENVIRONMENT", "development"),
)

app = Flask(__name__)
CORS(app)

api = Api(
    app,
    version="2.0",
    title="API Olist E-commerce",
    description=(
        "API REST connectée à MySQL exposant le dataset Olist Brazilian E-commerce.\n\n"
        "**Pipeline** : CSV brut → parsing → nettoyage → insertion MySQL → API Flask → Swagger\n\n"
        "**Tables disponibles** : clients, commandes, produits, vendeurs, paiements, avis, articles_commande\n\n"
        "**Source** : [Kaggle — Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)"
    ),
    doc="/swagger",
    contact="Olist API",
    license="MIT",
)

olist_ns = api.namespace(
    "olist",
    description="Endpoints du dataset Olist : statistiques, produits, commandes et analytics",
)

# ---------------------------------------------------------------------------
# Modèles Swagger (avec exemples sur chaque champ)
# ---------------------------------------------------------------------------

stats_model = api.model("Stats", {
    "nb_clients":   fields.Integer(description="Nombre total de clients",   example=99441),
    "nb_commandes": fields.Integer(description="Nombre total de commandes", example=99441),
    "nb_produits":  fields.Integer(description="Nombre total de produits",  example=32951),
    "nb_vendeurs":  fields.Integer(description="Nombre total de vendeurs",  example=3095),
    "nb_paiements": fields.Integer(description="Nombre total de paiements", example=103886),
    "nb_avis":      fields.Integer(description="Nombre total d'avis",       example=98371),
})

product_model = api.model("Produit", {
    "produit_id":  fields.String(description="Identifiant unique du produit (hash MD5)", example="1e9e8ef04dbcff4541ed26657ea517e5"),
    "categorie":   fields.String(description="Catégorie du produit en portugais",        example="perfumaria"),
    "poids_g":     fields.Float(description="Poids du produit en grammes",               example=225.0),
    "longueur_cm": fields.Float(description="Longueur de l'emballage en cm",             example=16.0),
    "hauteur_cm":  fields.Float(description="Hauteur de l'emballage en cm",              example=10.0),
    "largeur_cm":  fields.Float(description="Largeur de l'emballage en cm",              example=14.0),
})

order_model = api.model("Commande", {
    "commande_id": fields.String(description="Identifiant unique de la commande", example="e481f51cbdc54678b7cc49136f2d6af7"),
    "client_id":   fields.String(description="Identifiant du client associé",    example="9ef432eb6251297304e76186b10a928d"),
    "statut":      fields.String(description="Statut de la commande",            example="delivered"),
    "date_achat":  fields.String(description="Date et heure d'achat (ISO 8601)", example="2017-10-02T10:56:33"),
})

article_model = api.model("Article", {
    "produit_id":      fields.String(description="Identifiant du produit",          example="4244733e06e7ecb4970a6e2683c13e61"),
    "vendeur_id":      fields.String(description="Identifiant du vendeur",          example="48436dade18ac8b2bce089ec2a041202"),
    "prix":            fields.Float(description="Prix unitaire de l'article (BRL)", example=58.90),
    "frais_livraison": fields.Float(description="Frais de livraison (BRL)",         example=13.29),
})

paiement_model = api.model("Paiement", {
    "type_paiement": fields.String(description="Moyen de paiement",      example="credit_card"),
    "montant":       fields.Float(description="Montant payé (BRL)",      example=99.33),
    "nb_versements": fields.Integer(description="Nombre de versements",  example=3),
})

avis_model = api.model("Avis", {
    "note":        fields.Integer(description="Note de 1 à 5",    example=5),
    "titre":       fields.String(description="Titre de l'avis",   example="Produto chegou antes do prazo"),
    "commentaire": fields.String(description="Texte de l'avis",   example="Muito bom, recomendo!"),
})

order_detail_model = api.model("CommandeDetail", {
    "commande_id":            fields.String(description="Identifiant de la commande",         example="e481f51cbdc54678b7cc49136f2d6af7"),
    "statut":                 fields.String(description="Statut de la commande",              example="delivered"),
    "date_achat":             fields.String(description="Date d'achat (ISO 8601)",            example="2017-10-02T10:56:33"),
    "date_livraison":         fields.String(description="Date de livraison réelle",           example="2017-10-10T21:25:13"),
    "date_livraison_estimee": fields.String(description="Date de livraison estimée",         example="2017-10-18T00:00:00"),
    "ville":                  fields.String(description="Ville du client",                    example="franca"),
    "etat":                   fields.String(description="État brésilien du client (2 lettres)", example="SP"),
    "articles":  fields.List(fields.Nested(article_model),  description="Articles de la commande"),
    "paiements": fields.List(fields.Nested(paiement_model), description="Paiements associés"),
    "avis":      fields.List(fields.Nested(avis_model),     description="Avis du client"),
})

revenue_model = api.model("RevenueParEtat", {
    "etat":             fields.String(description="Code de l'État brésilien (2 lettres)", example="SP"),
    "chiffre_affaires": fields.Float(description="Chiffre d'affaires total en BRL",       example=5924786.62),
    "nb_commandes":     fields.Integer(description="Nombre de commandes dans cet État",   example=41746),
})

category_model = api.model("TopCategorie", {
    "categorie":     fields.String(description="Nom de la catégorie (en portugais)", example="cama_mesa_banho"),
    "nb_ventes":     fields.Integer(description="Nombre d'articles vendus",          example=11115),
    "revenus_total": fields.Float(description="Revenus totaux en BRL",               example=1800841.28),
})

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@olist_ns.route("/stats")
class Stats(Resource):
    @olist_ns.doc(description="Retourne le nombre total de lignes dans chaque table MySQL du dataset.")
    @olist_ns.marshal_with(stats_model)
    @olist_ns.response(200, "Succès — statistiques retournées", stats_model)
    @olist_ns.response(500, "Erreur de connexion MySQL")
    def get(self):
        """Statistiques globales du dataset (compteurs par table)"""
        return get_stats()


@olist_ns.route("/products")
class ProductList(Resource):
    @olist_ns.doc(description="Retourne les 100 premiers produits avec leurs dimensions et catégorie.")
    @olist_ns.marshal_list_with(product_model)
    @olist_ns.response(200, "Succès — liste de produits", [product_model])
    @olist_ns.response(500, "Erreur de connexion MySQL")
    def get(self):
        """Liste des 100 premiers produits"""
        return get_products(limit=100)


@olist_ns.route("/orders")
class OrderList(Resource):
    @olist_ns.doc(description="Retourne les 100 premières commandes avec leur statut et date d'achat.")
    @olist_ns.marshal_list_with(order_model)
    @olist_ns.response(200, "Succès — liste de commandes", [order_model])
    @olist_ns.response(500, "Erreur de connexion MySQL")
    def get(self):
        """Liste des 100 premières commandes"""
        return get_orders(limit=100)


@olist_ns.route("/orders/<string:order_id>")
@olist_ns.param("order_id", "Identifiant unique de la commande (ex: e481f51cbdc54678b7cc49136f2d6af7)")
class OrderDetail(Resource):
    @olist_ns.doc(description=(
        "Retourne le détail complet d'une commande : informations client, "
        "liste des articles achetés, paiements effectués et avis laissé.\n\n"
        "Récupérez un `commande_id` valide via **GET /olist/orders**."
    ))
    @olist_ns.marshal_with(order_detail_model)
    @olist_ns.response(200, "Succès — détail de la commande", order_detail_model)
    @olist_ns.response(404, "Commande introuvable")
    @olist_ns.response(500, "Erreur de connexion MySQL")
    def get(self, order_id):
        """Détail complet d'une commande (articles, paiements, avis)"""
        order = get_order_detail(order_id)
        if order is None:
            api.abort(404, f"Commande '{order_id}' introuvable")
        return order


@olist_ns.route("/analytics/revenue-by-state")
class RevenueByState(Resource):
    @olist_ns.doc(description=(
        "Agrégation SQL : somme des paiements groupée par État brésilien, "
        "triée par chiffre d'affaires décroissant.\n\n"
        "Utilise une jointure entre `commandes`, `clients` et `paiements`."
    ))
    @olist_ns.marshal_list_with(revenue_model)
    @olist_ns.response(200, "Succès — CA par État", [revenue_model])
    @olist_ns.response(500, "Erreur de connexion MySQL")
    def get(self):
        """Chiffre d'affaires total par État brésilien (trié par CA décroissant)"""
        return get_revenue_by_state()


@olist_ns.route("/analytics/top-categories")
class TopCategories(Resource):
    @olist_ns.doc(description=(
        "Classement des 10 catégories de produits les plus vendues, "
        "avec le nombre de ventes et les revenus totaux.\n\n"
        "Utilise une jointure entre `articles_commande` et `produits`."
    ))
    @olist_ns.marshal_list_with(category_model)
    @olist_ns.response(200, "Succès — top catégories", [category_model])
    @olist_ns.response(500, "Erreur de connexion MySQL")
    def get(self):
        """Top 10 des catégories les plus vendues (par nombre de ventes)"""
        return get_top_categories(limit=10)


# ---------------------------------------------------------------------------
# Route de test Sentry (vérification 4)
# ---------------------------------------------------------------------------

@olist_ns.route("/debug-sentry")
class DebugSentry(Resource):
    @olist_ns.doc(description="Déclenche volontairement une ZeroDivisionError pour tester Sentry.")
    @olist_ns.response(500, "Erreur volontaire envoyée à Sentry")
    def get(self):
        """Test Sentry — provoque une erreur volontaire (ZeroDivisionError)"""
        # division_by_zero = 1 / 0
        return {"message": "jamais atteint"}


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
