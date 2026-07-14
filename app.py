from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
@app.route("/", methods=["GET"])
def index():
    return "Servidor de Stock DIRESA activo. Usa /ver para visualizar los datos."
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
        items = datos["items"]
        conn = sqlite3.connect("stock.db")
        cur = conn.cursor()
        cur.execute("DELETE FROM stock WHERE puesto = ?", (puesto,))
        insert_data = [(puesto, i["codigo"], i["cantidad"], i["fecha"]) for i in items]
        cur.executemany("INSERT INTO stock (puesto, codigo, cantidad, fecha) VALUES (?, ?, ?, ?)", insert_data)
        conn.commit()
        conn.close()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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

@app.route("/ver", methods=["GET"])
def ver_tabla():
    conn = sqlite3.connect("stock.db")
    cur = conn.cursor()
    cur.execute("SELECT puesto, codigo, cantidad, fecha FROM stock ORDER BY puesto, codigo")
    filas = cur.fetchall()
    conn.close()

    html = """
    <html>
    <head>
        <meta charset='utf-8'>
        <title>Stock Consolidado - DIRESA Huancavelica</title>
        <style>
            body { font-family: Arial; margin: 20px; background: #f0f0f0; }
            h2 { color: #003366; text-align: center; }
            p { text-align: center; color: #555; }
            table { border-collapse: collapse; width: 100%; background: white; }
            th { background-color: #003366; color: white; padding: 10px; text-align: center; }
            td { border: 1px solid #ccc; padding: 8px; text-align: center; }
            tr:nth-child(even) { background-color: #e8f0fe; }
            tr:hover { background-color: #d0e4ff; }
        </style>
    </head>
    <body>
        <h2>Stock Consolidado - DIRESA 013 Huancavelica</h2>
        <p>Total de registros: """ + str(len(filas)) + """</p>
        <table>
            <tr>
                <th>#</th>
                <th>Puesto (ALMCOD)</th>
                <th>Código Medicamento</th>
                <th>Cantidad</th>
                <th>Fecha Actualización</th>
            </tr>
    """

    for i, f in enumerate(filas, 1):
        html += f"""
            <tr>
                <td>{i}</td>
                <td>{f[0]}</td>
                <td>{f[1]}</td>
                <td>{f[2]}</td>
                <td>{f[3]}</td>
            </tr>
        """

    html += """
        </table>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=10000, debug=False)
