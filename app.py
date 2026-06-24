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

app = Flask(__name__)
CORS(app)

api = Api(
    app,
    version="2.0",
    title="API Olist E-commerce",
    description="API Flask connectée à MySQL — dataset Olist Brazilian E-commerce",
    doc="/swagger",
)

olist_ns = api.namespace("olist", description="Données Olist E-commerce")

# ---------------------------------------------------------------------------
# Modèles Swagger
# ---------------------------------------------------------------------------

stats_model = api.model("Stats", {
    "nb_clients":   fields.Integer(description="Nombre de clients"),
    "nb_commandes": fields.Integer(description="Nombre de commandes"),
    "nb_produits":  fields.Integer(description="Nombre de produits"),
    "nb_vendeurs":  fields.Integer(description="Nombre de vendeurs"),
    "nb_paiements": fields.Integer(description="Nombre de paiements"),
    "nb_avis":      fields.Integer(description="Nombre d'avis"),
})

product_model = api.model("Produit", {
    "produit_id":   fields.String(description="Identifiant du produit"),
    "categorie":    fields.String(description="Catégorie"),
    "poids_g":      fields.Float(description="Poids en grammes"),
    "longueur_cm":  fields.Float(description="Longueur en cm"),
    "hauteur_cm":   fields.Float(description="Hauteur en cm"),
    "largeur_cm":   fields.Float(description="Largeur en cm"),
})

order_model = api.model("Commande", {
    "commande_id": fields.String(description="Identifiant de la commande"),
    "client_id":   fields.String(description="Identifiant du client"),
    "statut":      fields.String(description="Statut de la commande"),
    "date_achat":  fields.String(description="Date d'achat"),
})

article_model = api.model("Article", {
    "produit_id":      fields.String(),
    "vendeur_id":      fields.String(),
    "prix":            fields.Float(),
    "frais_livraison": fields.Float(),
})

paiement_model = api.model("Paiement", {
    "type_paiement": fields.String(),
    "montant":       fields.Float(),
    "nb_versements": fields.Integer(),
})

avis_model = api.model("Avis", {
    "note":        fields.Integer(),
    "titre":       fields.String(),
    "commentaire": fields.String(),
})

order_detail_model = api.model("CommandeDetail", {
    "commande_id":            fields.String(),
    "statut":                 fields.String(),
    "date_achat":             fields.String(),
    "date_livraison":         fields.String(),
    "date_livraison_estimee": fields.String(),
    "ville":                  fields.String(),
    "etat":                   fields.String(),
    "articles":  fields.List(fields.Nested(article_model)),
    "paiements": fields.List(fields.Nested(paiement_model)),
    "avis":      fields.List(fields.Nested(avis_model)),
})

revenue_model = api.model("RevenueParEtat", {
    "etat":             fields.String(description="Code de l'État brésilien"),
    "chiffre_affaires": fields.Float(description="CA total en BRL"),
    "nb_commandes":     fields.Integer(description="Nombre de commandes"),
})

category_model = api.model("TopCategorie", {
    "categorie":     fields.String(description="Nom de la catégorie"),
    "nb_ventes":     fields.Integer(description="Nombre d'articles vendus"),
    "revenus_total": fields.Float(description="Revenus totaux en BRL"),
})

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@olist_ns.route("/stats")
class Stats(Resource):
    @olist_ns.marshal_with(stats_model)
    def get(self):
        """Statistiques globales du dataset"""
        return get_stats()


@olist_ns.route("/products")
class ProductList(Resource):
    @olist_ns.marshal_list_with(product_model)
    def get(self):
        """Liste des produits (100 premiers)"""
        return get_products(limit=100)


@olist_ns.route("/orders")
class OrderList(Resource):
    @olist_ns.marshal_list_with(order_model)
    def get(self):
        """Liste des commandes (100 premières)"""
        return get_orders(limit=100)


@olist_ns.route("/orders/<string:order_id>")
class OrderDetail(Resource):
    @olist_ns.marshal_with(order_detail_model)
    def get(self, order_id):
        """Détail complet d'une commande (articles, paiements, avis)"""
        order = get_order_detail(order_id)
        if order is None:
            api.abort(404, f"Commande {order_id} introuvable")
        return order


@olist_ns.route("/analytics/revenue-by-state")
class RevenueByState(Resource):
    @olist_ns.marshal_list_with(revenue_model)
    def get(self):
        """Chiffre d'affaires par État brésilien"""
        return get_revenue_by_state()


@olist_ns.route("/analytics/top-categories")
class TopCategories(Resource):
    @olist_ns.marshal_list_with(category_model)
    def get(self):
        """Top 10 des catégories les plus vendues"""
        return get_top_categories(limit=10)


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
