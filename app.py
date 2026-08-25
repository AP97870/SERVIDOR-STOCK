@app.route("/consolidado", methods=["GET"])
def consolidado():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT TRIM(s.puesto) as puesto,
                   COALESCE(NULLIF(TRIM(e.name), ''), 'SIN NOMBRE') as name,
                   COALESCE(NULLIF(TRIM(e.red), ''), '') as red,
                   COALESCE(NULLIF(TRIM(e.microred), ''), '') as microred,
                   s.codigo, s.cantidad, s.medregsan, s.medlote,
                   s.fecha, s.fecha_envio
            FROM stock s
            LEFT JOIN "ESTABLECIMIENTOS" e
                   ON TRIM(e.cod_pre) = TRIM(s.puesto)
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

@app.route("/envios-por-puesto", methods=["GET"])
def envios_por_puesto():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT TRIM(s.puesto) as puesto,
                   COALESCE(NULLIF(TRIM(e.name), ''), 'SIN NOMBRE') as nombre,
                   COUNT(*) as total_items,
                   SUM(CASE WHEN s.cantidad > 0 THEN 1 ELSE 0 END) as con_stock,
                   MAX(s.fecha_envio) as ult_envio
            FROM stock s
            LEFT JOIN "ESTABLECIMIENTOS" e ON TRIM(e.cod_pre) = TRIM(s.puesto)
            GROUP BY TRIM(s.puesto), TRIM(e.name)
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
