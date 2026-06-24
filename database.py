import mysql.connector
# On importe le connecteur MySQL pour permettre à Python de communiquer avec la base de données.

def get_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="ynov-db",
        port=3306,
    )
    # Increase packet size to 64MB for the current session
    cursor = conn.cursor()
    cursor.execute("SET GLOBAL max_allowed_packet = 67108864")
    cursor.close()
    return conn