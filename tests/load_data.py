import csv
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "esculturas-publicas-medellin-limpio.csv")

def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT", 5432),
        sslmode=os.getenv("POSTGRES_SSLMODE", "require")
    )

def load_data():
    conn = get_connection()
    cur = conn.cursor()

    with open(CSV_PATH, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            # Insertar autor (si no existe)
            cur.execute(
                "INSERT INTO autores (nombre) VALUES (%s) ON CONFLICT (nombre) DO NOTHING RETURNING id;",
                (row["author"],),
            )
            autor_id = cur.fetchone()
            if not autor_id:
                cur.execute("SELECT id FROM autores WHERE nombre = %s;", (row["author"],))
                autor_id = cur.fetchone()
            autor_id = autor_id[0]

            # Insertar obra
            cur.execute(
                """
                INSERT INTO obras (nombre, autor_id, anio, tipo, comuna, barrio, direccion, descripcion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
                """,
                (
                    row["name"],
                    autor_id,
                    int(row["year"]) if row["year"].isdigit() else None,
                    row.get("type"),
                    row.get("area"),  # usar 'area' como comuna
                    None,  # barrio no está en el CSV
                    row.get("general-direction"),
                    None,  # descripcion no está en el CSV
                ),
            )

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Datos cargados en la base de datos.")

if __name__ == "__main__":
    load_data()
