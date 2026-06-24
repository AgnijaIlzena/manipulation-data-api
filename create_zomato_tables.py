from database import get_connection
from pathlib import Path

def create_zomato_tables():
    sql = Path("schema_zomato.sql").read_text(encoding="utf-8")
    statements = [s.strip() for s in sql.split(";") if s.strip()]

    conn = get_connection()
    cursor = conn.cursor()

    for statement in statements:
        cursor.execute(statement)
        label = statement.split("\n")[0][:60]
        print(f"OK: {label}")

    conn.commit()
    cursor.close()
    conn.close()
    print("\nTables Zomato creees avec succes.")

if __name__ == "__main__":
    create_zomato_tables()
