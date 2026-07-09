from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("stock.db")
    cur = conn.cursor()
    # Eliminado campo 'descripcion' para coincidir con tu tabla real
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
        items = datos["items"]
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect("stock.db")
        cur = conn.cursor()

        # Usamos una transacción para asegurar la integridad
        cur.execute("BEGIN TRANSACTION")
        cur.execute("DELETE FROM stock WHERE puesto = ?", (puesto,))

        # Preparar los datos para una inserción masiva (mucho más rápido)
        insert_data = [
            (puesto, item["codigo"], item["cantidad"], item["fecha"]) 
            for item in items
        ]
        
        cur.executemany("""
            INSERT INTO stock (puesto, codigo, cantidad, fecha)
            VALUES (?, ?, ?, ?)
        """, insert_data)

        conn.commit()
        conn.close()

        return jsonify({"status": "ok", "puesto": puesto, "items_procesados": len(items)})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/stock", methods=["GET"])
def ver_stock():
    conn = sqlite3.connect("stock.db")
    cur = conn.cursor()
    cur.execute("SELECT puesto, codigo, cantidad, fecha FROM stock ORDER BY puesto")
    filas = cur.fetchall()
    conn.close()

    resultado = [
        {"puesto": f[0], "codigo": f[1], "cantidad": f[2], "fecha": f[3]} 
        for f in filas
    ]

    return jsonify(resultado)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=10000, debug=False)
