import pytest
from unittest.mock import patch
from app import app

MOCK_PRODUCTS = [
    {
        "produit_id": "1e9e8ef04dbcff4541ed26657ea517e5",
        "categorie": "perfumaria",
        "poids_g": 225.0,
        "longueur_cm": 16.0,
        "hauteur_cm": 10.0,
        "largeur_cm": 14.0,
    },
    {
        "produit_id": "3aa071139cb16b67ca9e5dea641aaa2f",
        "categorie": "artes",
        "poids_g": 1000.0,
        "longueur_cm": 30.0,
        "hauteur_cm": 18.0,
        "largeur_cm": 20.0,
    },
]


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_products_status_200(client):
    """GET /olist/products doit retourner HTTP 200."""
    with patch("app.get_products", return_value=MOCK_PRODUCTS):
        res = client.get("/olist/products")
        assert res.status_code == 200


def test_products_returns_list(client):
    """La réponse doit être une liste JSON."""
    with patch("app.get_products", return_value=MOCK_PRODUCTS):
        data = client.get("/olist/products").get_json()
        assert isinstance(data, list)
        assert len(data) == 2


def test_product_has_required_fields(client):
    """Chaque produit doit contenir les 6 champs attendus."""
    required = ["produit_id", "categorie", "poids_g", "longueur_cm", "hauteur_cm", "largeur_cm"]
    with patch("app.get_products", return_value=MOCK_PRODUCTS):
        product = client.get("/olist/products").get_json()[0]
        for field in required:
            assert field in product, f"Champ manquant : {field}"


def test_product_id_is_string(client):
    """produit_id doit être une chaîne de caractères."""
    with patch("app.get_products", return_value=MOCK_PRODUCTS):
        product = client.get("/olist/products").get_json()[0]
        assert isinstance(product["produit_id"], str)


def test_product_weight_is_number(client):
    """poids_g doit être un nombre."""
    with patch("app.get_products", return_value=MOCK_PRODUCTS):
        product = client.get("/olist/products").get_json()[0]
        assert isinstance(product["poids_g"], (int, float))
