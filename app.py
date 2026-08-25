from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import psycopg2
import csv
import io
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB_URI = "postgresql://postgres.gmipdeiarpubwcsfhrhk:server4597841@aws-0-ca-central-1.pooler.supabase.com:6543/postgres?sslmode=require"

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
                fecha_envio DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    return jsonify({
        "servidor": "DIRESA Huancavelica - Red Tayacaja",
        "estado": "activo",
        "timestamp": datetime.now().isoformat(),
        "endpoints": ["/recibir", "/descargar", "/ver", "/consolidado", "/estadisticas", "/envios-por-puesto", "/resumen-por-estado"]
    })

@app.route("/recibir", methods=["POST"])
def recibir():
    try:
        datos = request.get_json()
        puesto = datos.get("puesto", "SIN_PUESTO")
        items = datos.get("items", [])

        if not items:
            return jsonify({"status": "error", "message": "No se recibieron items"}), 400

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
                fecha_envio = EXCLUDED.fecha_envio,
                created_at = CURRENT_TIMESTAMP;
        """

        for i in items:
            cur.execute(sql_upsert, (
                puesto,
                i.get("codigo"),
                i.get("cantidad"),
                i.get("fecha"),
                i.get("medregsan"),
                i.get("medlote"),
                i.get("fecha_envio")
            ))

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "ok", "items_procesados": len(items)}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/descargar")
def descargar_csv():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT puesto, codigo, cantidad, fecha, medregsan, medlote, fecha_envio FROM stock ORDER BY puesto, codigo")
        filas = cur.fetchall()
        cur.close()
        conn.close()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Puesto', 'Codigo', 'Cantidad', 'Fecha', 'RegSanitario', 'Lote', 'Fecha Envio'])

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
            <style>
                body { font-family: 'Segoe UI', sans-serif; margin: 20px; background: #f4f6f9; }
                h2 { color: #0f4c81; }
                .toolbar { margin-bottom: 15px; }
                .toolbar a { text-decoration: none; padding: 8px 16px; border-radius: 4px; margin-right: 10px; font-size: 13px; }
                .btn-download { background: #0f4c81; color: white; }
                .btn-clean { background: #dc3545; color: white; }
                .stats { background: white; padding: 10px 15px; border-radius: 4px; margin-bottom: 15px; display: inline-block; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
            </style>
        </head>
        <body>
            <h2>Stock Consolidado - DIRESA 013 Huancavelica</h2>
            <div class="toolbar">
                <a href="/descargar" class="btn-download">Descargar reporte (.csv)</a>
                <a href="/estadisticas" class="btn-download" style="background:#28a745;">Ver Estadisticas (JSON)</a>
                <a href="/limpiar" class="btn-clean" onclick="return confirm('Estas seguro de eliminar TODOS los registros?')">Limpiar Tabla</a>
            </div>
            <div class="stats">
                <strong>Total registros:</strong> """ + str(len(filas)) + """
            </div>
            <table id="miTablaStock" class="display">
                <thead>
                    <tr><th>Puesto</th><th>Codigo</th><th>Cantidad</th><th>Fecha</th><th>Reg. Sanitario</th><th>Lote</th><th>Fecha Envio</th></tr>
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
                        "paging": true,
                        "pageLength": 50,
                        "scrollY": "500px",
                        "scrollCollapse": true,
                        "ordering": true,
                        "language": { "url": "//cdn.datatables.net/plug-ins/1.11.5/i18n/es-ES.json" }
                    });
                });
            </script>
        </body>
        </html>
        """
        return html
    except Exception as e:
        return f"Error en la visualizacion: {str(e)}", 500

@app.route("/limpiar", methods=["GET"])
def limpiar_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM stock")
        conn.commit()
        cur.close()
        conn.close()
        return "Base de datos limpiada con exito. <a href='/ver'>Volver al reporte</a>"
    except Exception as e:
        return f"Error al limpiar: {str(e)}", 500

@app.route("/consolidado", methods=["GET"])
def consolidado():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT s.puesto,
                   e.name,
                   e.red,
                   e.microred,
                   s.codigo, s.cantidad, s.medregsan, s.medlote,
                   s.fecha, s.fecha_envio
            FROM stock s
            LEFT JOIN "ESTABLECIMIENTOS" e
                   ON e.cod_pre = s.puesto
            ORDER BY s.puesto, s.codigo
        """)
        filas = cur.fetchall()
        cur.close()
        conn.close()

        data = []
        for f in filas:
            data.append({
                "puesto": f[0] or "",
                "nombre": f[1] or "",
                "red": f[2] or "",
                "microrred": f[3] or "",
                "codigo": f[4] or "",
                "cantidad": float(f[5]) if f[5] is not None else 0,
                "medregsan": f[6] or "",
                "medlote": f[7] or "",
                "fecha": f[8] or "",
                "fecha_envio": str(f[9]) if f[9] is not None else ""
            })
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/estadisticas", methods=["GET"])
def estadisticas():
    """Devuelve estadisticas resumidas del stock"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Total de registros
        cur.execute("SELECT COUNT(*) FROM stock")
        total_registros = cur.fetchone()[0]
        
        # Total de puestos unicos
        cur.execute("SELECT COUNT(DISTINCT puesto) FROM stock")
        total_puestos = cur.fetchone()[0]
        
        # Total de productos unicos
        cur.execute("SELECT COUNT(DISTINCT codigo) FROM stock")
        total_productos = cur.fetchone()[0]
        
        # Ultimos 10 envios
        cur.execute("""
            SELECT puesto, MAX(fecha_envio) as ult_envio, COUNT(*) as items 
            FROM stock 
            GROUP BY puesto 
            ORDER BY ult_envio DESC 
            LIMIT 10
        """)
        ultimos_envios = []
        for row in cur.fetchall():
            ultimos_envios.append({
                "puesto": row[0],
                "ultimo_envio": str(row[1]) if row[1] else "",
                "items": row[2]
            })
        
        cur.close()
        conn.close()
        
        return jsonify({
            "total_registros": total_registros,
            "total_puestos": total_puestos,
            "total_productos": total_productos,
            "ultimos_envios": ultimos_envios,
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/envios-por-puesto", methods=["GET"])
def envios_por_puesto():
    """Devuelve un resumen por puesto: cuantos items, ultima fecha"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT s.puesto,
                   e.name as nombre,
                   COUNT(*) as total_items,
                   SUM(CASE WHEN s.cantidad > 0 THEN 1 ELSE 0 END) as con_stock,
                   MAX(s.fecha_envio) as ult_envio
            FROM stock s
            LEFT JOIN "ESTABLECIMIENTOS" e ON e.cod_pre = s.puesto
            GROUP BY s.puesto, e.name
            ORDER BY ult_envio DESC
        """)
        filas = cur.fetchall()
        cur.close()
        conn.close()

        data = []
        for f in filas:
            total = f[2] or 0
            con_stock = f[3] or 0
            pct = (con_stock / total * 100) if total > 0 else 0
            data.append({
                "puesto": f[0] or "",
                "nombre": f[1] or "",
                "total_items": total,
                "con_stock": con_stock,
                "pct_disponibilidad": round(pct, 2),
                "ultimo_envio": str(f[4]) if f[4] else ""
            })
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/resumen-por-estado", methods=["GET"])
def resumen_por_estado():
    """Agrupa productos por rangos de cantidad para detectar desabastecimiento"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                SUM(CASE WHEN cantidad = 0 THEN 1 ELSE 0 END) as desabastecido,
                SUM(CASE WHEN cantidad > 0 AND cantidad <= 10 THEN 1 ELSE 0 END) as critico,
                SUM(CASE WHEN cantidad > 10 AND cantidad <= 50 THEN 1 ELSE 0 END) as bajo,
                SUM(CASE WHEN cantidad > 50 THEN 1 ELSE 0 END) as normal
            FROM stock
        """)
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        return jsonify({
            "desabastecido": row[0] or 0,
            "critico": row[1] or 0,
            "bajo": row[2] or 0,
            "normal": row[3] or 0
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "db": "connected"}), 200

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=10000, debug=False)
