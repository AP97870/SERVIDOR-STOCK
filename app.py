from flask import Flask, request, jsonify, Response
import sqlite3
import csv
import io

app = Flask(__name__)

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

@app.route("/", methods=["GET"])
def index():
    return "Servidor DIRESA Huancavelica Activo. Usa /ver para visualizar el Grid."

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

@app.route("/descargar")
def descargar_csv():
    conn = sqlite3.connect("stock.db")
    cur = conn.cursor()
    cur.execute("SELECT puesto, codigo, cantidad, fecha FROM stock")
    filas = cur.fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Puesto', 'Codigo', 'Cantidad', 'Fecha'])
    writer.writerows(filas)
    output.seek(0)
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=stock_diresa.csv"})

@app.route("/ver", methods=["GET"])
def ver_tabla():
    conn = sqlite3.connect("stock.db")
    cur = conn.cursor()
    cur.execute("SELECT puesto, codigo, cantidad, fecha FROM stock ORDER BY puesto, codigo")
    filas = cur.fetchall()
    conn.close()

    html = f"""
    <html>
    <head>
        <meta charset='utf-8'>
        <title>Stock - DIRESA Huancavelica</title>
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.css">
        <script type="text/javascript" src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script type="text/javascript" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
        <style>
            body {{ font-family: Arial; margin: 20px; background: #f4f7f6; }}
            h2 {{ color: #003366; }}
            .btn-descarga {{ background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <h2>Stock Consolidado - DIRESA Huancavelica</h2>
        <a href="/descargar" class="btn-descarga">📥 Descargar a Excel (CSV)</a>
        <table id="miTablaStock" class="display">
            <thead>
                <tr><th>Puesto</th><th>Código</th><th>Cantidad</th><th>Fecha</th></tr>
            </thead>
            <tbody>
    """
    for f in filas:
        html += f"<tr><td>{f[0]}</td><td>{f[1]}</td><td>{f[2]}</td><td>{f[3]}</td></tr>"
    
    html += """
            </tbody>
        </table>
        <script>
            $(document).ready( function () {
                $('#miTablaStock').DataTable({ "language": { "url": "//cdn.datatables.net/plug-ins/1.11.5/i18n/es-ES.json" } });
            });
        </script>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=10000, debug=False)
