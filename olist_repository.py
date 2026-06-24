from database import get_connection


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
