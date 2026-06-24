from database import get_connection
# On importe la fonction get_connection depuis le fichier database.py.
# Cette fonction sert à ouvrir une connexion avec la base MySQL.


def get_all_products():
    # On définit une fonction qui va récupérer tous les produits.

    connexion = get_connection()
    # On ouvre une connexion avec la base de données MySQL.

    curseur = connexion.cursor(dictionary=True)
    # On crée un curseur pour exécuter des requêtes SQL.
    # dictionary=True permet de récupérer les résultats sous forme de dictionnaire.
    # Exemple : {"id": 1, "nom": "Clavier", "prix": 49.99, "stock": 10}

    curseur.execute("SELECT id, nom, prix, stock FROM produits")
    # On exécute une requête SQL SELECT.
    # Cette requête récupère les colonnes id, nom, prix et stock dans la table produits.

    produits = curseur.fetchall()
    # fetchall() récupère toutes les lignes retournées par la requête SQL.
    # Le résultat est une liste de produits.

    curseur.close()
    # On ferme le curseur car on n’en a plus besoin.

    connexion.close()
    # On ferme la connexion avec MySQL pour libérer les ressources.

    return produits
    # On retourne la liste des produits à la route API.


def get_product_by_id(product_id):
    # On définit une fonction qui récupère un produit précis grâce à son id.

    connexion = get_connection()
    # On ouvre une connexion avec la base MySQL.

    curseur = connexion.cursor(dictionary=True)
    # On crée un curseur qui retourne les résultats sous forme de dictionnaire.

    sql = "SELECT id, nom, prix, stock FROM produits WHERE id = %s"
    # On prépare une requête SQL SELECT avec une condition WHERE.
    # WHERE id = %s permet de cibler uniquement le produit demandé.
    # Le %s est un emplacement sécurisé pour une valeur.

    curseur.execute(sql, (product_id,))
    # On exécute la requête SQL en remplaçant %s par product_id.
    # (product_id,) est un tuple Python avec une seule valeur.
    # La virgule est obligatoire dans un tuple à une seule valeur.

    produit = curseur.fetchone()
    # fetchone() récupère une seule ligne.
    # Si aucun produit ne correspond à l’id, la valeur retournée sera None.

    curseur.close()
    # On ferme le curseur.

    connexion.close()
    # On ferme la connexion avec MySQL.

    return produit
    # On retourne le produit trouvé à la route API.
    # Si aucun produit n’est trouvé, on retourne None.


def create_product(nom, prix, stock):
    # On définit une fonction qui ajoute un nouveau produit dans la base.

    connexion = get_connection()
    # On ouvre une connexion avec MySQL.

    curseur = connexion.cursor()
    # On crée un curseur pour exécuter la requête d’insertion.

    sql = "INSERT INTO produits (nom, prix, stock) VALUES (%s, %s, %s)"
    # On prépare une requête SQL INSERT.
    # Cette requête ajoute une nouvelle ligne dans la table produits.
    # Les trois %s correspondent au nom, au prix et au stock.

    valeurs = (nom, prix, stock)
    # On prépare les valeurs à insérer dans la base.
    # Les valeurs sont placées dans un tuple Python.

    curseur.execute(sql, valeurs)
    # On exécute la requête SQL avec les valeurs données.
    # MySQL remplace les %s par les valeurs du tuple.

    connexion.commit()
    # commit() valide l’insertion dans la base de données.
    # Sans commit(), l’ajout peut ne pas être enregistré.

    new_id = curseur.lastrowid
    # lastrowid récupère l’identifiant du produit qui vient d’être créé.

    curseur.close()
    # On ferme le curseur.

    connexion.close()
    # On ferme la connexion avec MySQL.

    return new_id
    # On retourne l’id du nouveau produit à l’API.


def update_product(product_id, nom, prix, stock):
    # On définit une fonction qui modifie un produit existant.

    connexion = get_connection()
    # On ouvre une connexion avec MySQL.

    curseur = connexion.cursor()
    # On crée un curseur pour exécuter la requête de modification.

    sql = "UPDATE produits SET nom = %s, prix = %s, stock = %s WHERE id = %s"
    # On prépare une requête SQL UPDATE.
    # SET indique les colonnes à modifier.
    # WHERE id = %s permet de modifier uniquement le produit ciblé.
    # Sans WHERE, tous les produits pourraient être modifiés.

    valeurs = (nom, prix, stock, product_id)
    # On prépare les nouvelles valeurs.
    # L’ordre doit correspondre aux %s de la requête SQL.

    curseur.execute(sql, valeurs)
    # On exécute la requête SQL avec les nouvelles valeurs.

    connexion.commit()
    # commit() valide la modification dans MySQL.

    lignes_modifiees = curseur.rowcount
    # rowcount indique combien de lignes ont été modifiées.
    # Si la valeur est 0, cela signifie qu’aucun produit avec cet id n’a été trouvé.

    curseur.close()
    # On ferme le curseur.

    connexion.close()
    # On ferme la connexion avec MySQL.

    return lignes_modifiees
    # On retourne le nombre de lignes modifiées à l’API.


def delete_product(product_id):
    # On définit une fonction qui supprime un produit grâce à son id.

    connexion = get_connection()
    # On ouvre une connexion avec MySQL.

    curseur = connexion.cursor()
    # On crée un curseur pour exécuter la requête de suppression.

    sql = "DELETE FROM produits WHERE id = %s"
    # On prépare une requête SQL DELETE.
    # WHERE id = %s permet de supprimer uniquement le produit ciblé.
    # Sans WHERE, tous les produits pourraient être supprimés.

    curseur.execute(sql, (product_id,))
    # On exécute la requête SQL en remplaçant %s par l’id du produit.
    # (product_id,) est un tuple avec une seule valeur.

    connexion.commit()
    # commit() valide la suppression dans MySQL.

    lignes_supprimees = curseur.rowcount
    # rowcount indique combien de lignes ont été supprimées.
    # Si la valeur est 0, aucun produit avec cet id n’existe.

    curseur.close()
    # On ferme le curseur.

    connexion.close()
    # On ferme la connexion avec MySQL.

    return lignes_supprimees
    # On retourne le nombre de lignes supprimées à l’API.