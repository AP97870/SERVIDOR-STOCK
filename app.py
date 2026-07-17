from flask import Flask, request, jsonify, Response
import psycopg2
import csv
import io
import json

app = Flask(__name__)

DB_URI = "postgresql://postgres:server4597841@db.gmipdeiarpubwcsfhrhk.supabase.co:5432/postgres"

def get_db_connection():
    return psycopg2.connect(DB_URI)

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stock (
                id SERIAL PRIMARY KEY,
                puesto TEXT,
                codigo TEXT,
                cantidad REAL,
                fecha TEXT,
                medregsan TEXT,
                medlote TEXT,
                fecha_envio DATE
            )
        """)
        cur.execute("""
            ALTER TABLE stock DROP CONSTRAINT IF EXISTS unique_puesto_codigo_lote;
            ALTER TABLE stock ADD CONSTRAINT unique_puesto_codigo_lote UNIQUE (puesto, codigo, medlote);
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error al inicializar: {str(e)}")

@app.route("/", methods=["GET"])
def index():
    return "Servidor DIRESA Huancavelica Activo."

@app.route("/recibir", methods=["POST"])
def recibir():
    try:
        datos = request.get_json()
        puesto = datos["puesto"]
        items = datos["items"]
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        sql_upsert = """
            INSERT INTO stock (puesto, codigo, cantidad, fecha, medregsan, medlote, fecha_envio)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (puesto, codigo, medlote) 
            DO UPDATE SET 
                cantidad = EXCLUDED.cantidad,
                fecha = EXCLUDED.fecha,
                medregsan = EXCLUDED.medregsan,
                fecha_envio = EXCLUDED.fecha_envio;
        """
        
        for i in items:
            cur.execute(sql_upsert, (puesto, i["codigo"], i["cantidad"], i["fecha"], i["medregsan"], i["medlote"], i.get("fecha_envio")))
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/descargar")
def descargar_csv():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT puesto, codigo, cantidad, fecha, medregsan, medlote, fecha_envio FROM stock")
        filas = cur.fetchall()
        cur.close()
        conn.close()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Puesto', 'Codigo', 'Cantidad', 'Fecha', 'RegSanitario', 'Lote', 'Fecha Envío'])
        
        filas_int = [(f[0], f[1], int(f[2]) if f[2] is not None else 0, f[3], f[4], f[5], f[6]) for f in filas]
        writer.writerows(filas_int)
        output.seek(0)
        return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=stock_diresa.csv"})
    except Exception as e:
        return f"Error al generar CSV: {str(e)}", 500

@app.route("/ver", methods=["GET"])
def ver_tabla():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT puesto, codigo, cantidad, fecha, medregsan, medlote, fecha_envio FROM stock ORDER BY puesto, codigo")
        filas = cur.fetchall()
        cur.close()
        conn.close()

        html = """
        <html>
        <head>
            <meta charset='utf-8'>
            <title>Reporte de Stock - DIRESA</title>
            <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.css">
            <script type="text/javascript" src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
            <script type="text/javascript" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
        </head>
        <body>
            <h2>Stock Consolidado - DIRESA 013 Huancavelica</h2>
            <a href="/descargar">📥 Descargar reporte (.csv)</a>
            <table id="miTablaStock" class="display">
                <thead>
                    <tr><th>Puesto</th><th>Código</th><th>Cantidad</th><th>Fecha</th><th>Reg. Sanitario</th><th>Lote</th><th>Fecha Envío</th></tr>
                </thead>
                <tbody>
        """
        for f in filas:
            puesto = f[0] or ""
            codigo = f[1] or ""
            cantidad = int(f[2]) if f[2] is not None else 0
            fecha = f[3] or ""
            regsan = f[4] or ""
            lote = f[5] or ""
            fecha_envio = str(f[6]) if f[6] is not None else ""
            
            html += f"<tr><td>{puesto}</td><td>{codigo}</td><td>{cantidad}</td><td>{fecha}</td><td>{regsan}</td><td>{lote}</td><td>{fecha_envio}</td></tr>"
        
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
                        "language": { "url": "//cdn.datatables.net/plug-ins/1.11.5/i18n/es-ES.json" }
                    });
                });
            </script>
        </body>
        </html>
        """
        return html
    except Exception as e:
        return f"Error en la visualización: {str(e)}", 500

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=10000, debug=False)
