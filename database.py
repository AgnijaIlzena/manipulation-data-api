import mysql.connector
# On importe le connecteur MySQL pour permettre à Python de communiquer avec la base de données.

def get_connection():
    # On crée une fonction réutilisable qui ouvre une connexion à MySQL.

    return mysql.connector.connect(
        # On retourne directement une connexion active.

        host="localhost",
        # Le serveur MySQL est installé sur la machine locale.

        user="root",
        # Utilisateur MySQL utilisé pour se connecter.

        password="",
        # Mot de passe MySQL.
        # Sur XAMPP/WAMP, il est souvent vide.
        # Sur MAMP, il est souvent "root".

        database="ynov-db",
        # Nom de la base de données utilisée par l’API.

        port=3306
        # Port par défaut du serveur MySQL.
    )