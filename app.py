from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Función para asegurar que la tabla existe
def init_db():
    conn = sqlite3.connect("stock.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            puesto TEXT,
            codigo TEXT,
            cantidad REAL,
            fecha TEXT
        )
    """)
    conn.commit()
    conn.close()

@app.route("/recibir", methods=["POST"])
def recibir():
    try:
        datos = request.get_json()
        puesto = datos["puesto"]
        items = datos["items"] # Esto debe ser una lista de objetos

        conn = sqlite3.connect("stock.db")
        cur = conn.cursor()
        
        # Eliminamos lo anterior del puesto y guardamos lo nuevo
        cur.execute("DELETE FROM stock WHERE puesto = ?", (puesto,))
        
        # Inserción masiva
        insert_data = [(puesto, i["codigo"], i["cantidad"], i["fecha"]) for i in items]
        cur.executemany("INSERT INTO stock (puesto, codigo, cantidad, fecha) VALUES (?, ?, ?, ?)", insert_data)
        
        conn.commit()
        conn.close()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
# --- ESTO ES LO QUE DEBES AGREGAR A TU app.py ---

@app.route("/stock", methods=["GET"])
def obtener_stock():
    try:
        conn = sqlite3.connect("stock.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM stock")
        datos = cur.fetchall()
        conn.close()
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=10000)
