from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(_name_)

def init_db():
    conn = sqlite3.connect("stock.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            puesto      TEXT,
            codigo      TEXT,
            descripcion TEXT,
            cantidad    REAL,
            fecha       TEXT
        )
    """)
    conn.commit()
    conn.close()

@app.route("/recibir", methods=["POST"])
def recibir():
    datos = request.get_json()
    puesto = datos["puesto"]
    items  = datos["items"]
    fecha  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect("stock.db")
    cur  = conn.cursor()

    cur.execute("DELETE FROM stock WHERE puesto = ?", (puesto,))

    for item in items:
        cur.execute("""
            INSERT INTO stock (puesto, codigo, descripcion, cantidad, fecha)
            VALUES (?, ?, ?, ?, ?)
        """, (puesto, item["codigo"], item["descripcion"], item["cantidad"], fecha))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok", "puesto": puesto, "items": len(items)})

@app.route("/stock", methods=["GET"])
def ver_stock():
    conn = sqlite3.connect("stock.db")
    cur  = conn.cursor()
    cur.execute("SELECT puesto, codigo, descripcion, cantidad, fecha FROM stock ORDER BY puesto")
    filas = cur.fetchall()
    conn.close()

    resultado = []
    for f in filas:
        resultado.append({
            "puesto": f[0],
            "codigo": f[1],
            "descripcion": f[2],
            "cantidad": f[3],
            "fecha": f[4]
        })

    return jsonify(resultado)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=10000, debug=False)
