from flask import Flask, request, jsonify, Response
import sqlite3
import csv
import io
import json

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("stock.db")
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS stock")
    cur.execute("""
        CREATE TABLE stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            puesto TEXT,
            codigo TEXT,
            cantidad REAL,
            fecha TEXT,
            medregsan TEXT,
            medlote TEXT
        )
    """)
    conn.commit()
    conn.close()

@app.route("/", methods=["GET"])
def index():
    return "Servidor DIRESA Huancavelica Activo. Usa /ver para visualizar el reporte."

@app.route("/recibir", methods=["POST"])
def recibir():
    try:
        datos = request.get_json()
        puesto = datos["puesto"]
        items = datos["items"]
        
        conn = sqlite3.connect("stock.db")
        cur = conn.cursor()
        
        insert_data = [
            (puesto, i["codigo"], i["cantidad"], i["fecha"], i["medregsan"], i["medlote"]) 
            for i in items
        ]
        
        cur.executemany("""
            INSERT INTO stock (puesto, codigo, cantidad, fecha, medregsan, medlote) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, insert_data)
        
        conn.commit()
        conn.close()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/descargar")
def descargar_csv():
    conn = sqlite3.connect("stock.db")
    cur = conn.cursor()
    cur.execute("SELECT puesto, codigo, cantidad, fecha, medregsan, medlote FROM stock")
    filas = cur.fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Puesto', 'Codigo', 'Cantidad', 'Fecha', 'RegSanitario', 'Lote'])
    
    filas_int = [(f[0], f[1], int(f[2]) if f[2] is not None else 0, f[3], f[4], f[5]) for f in filas]
    writer.writerows(filas_int)
    output.seek(0)
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=stock_diresa.csv"})

@app.route("/ver", methods=["GET"])
def ver_tabla():
    conn = sqlite3.connect("stock.db")
    cur = conn.cursor()
    cur.execute("SELECT puesto, codigo, cantidad, fecha, medregsan, medlote FROM stock ORDER BY puesto, codigo")
    filas = cur.fetchall()
    conn.close()

    html = f"""
    <html>
    <head>
        <meta charset='utf-8'>
        <title>Reporte de Stock - DIRESA</title>
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.css">
        <script type="text/javascript" src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script type="text/javascript" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
        <style>
            table.dataTable.dtr-inline.collapsed > tbody > tr > td:first-child:before { display: none !important; }
        </style>
    </head>
    <body>
        <h2>Stock Consolidado - DIRESA 013 Huancavelica</h2>
        <a href="/descargar">📥 Descargar reporte (.csv)</a>
        <table id="miTablaStock" class="display">
            <thead>
                <tr><th>Puesto</th><th>Código</th><th>Cantidad</th><th>Fecha</th><th>Reg. Sanitario</th><th>Lote</th></tr>
            </thead>
            <tbody>
    """
    for f in filas:
        cantidad = int(f[2]) if f[2] is not None else 0
        # Muestra el código de puesto tal cual llega desde la base de datos
        html += f"<tr><td>{f[0]}</td><td>{f[1]}</td><td>{cantidad}</td><td>{f[3]}</td><td>{f[4]}</td><td>{f[5]}</td></tr>"
    
    html += """
            </tbody>
        </table>
        <script>
            $(document).ready( function () {
                $('#miTablaStock').DataTable({
                    "paging": false,
                    "scrollY": "600px",
                    "scrollCollapse": true,
                    "ordering": false,
                    "responsive": false,
                    "columns": [null, null, null, null, null, null],
                    "language": { "url": "//cdn.datatables.net/plug-ins/1.11.5/i18n/es-ES.json" }
                });
            });
        </script>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=10000, debug=False)
