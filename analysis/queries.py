import sqlite3
from tabulate import tabulate


class AnalysisQueries:
    def __init__(self, db_path='database/ecommerce.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        return self

    def close(self):
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def print_result(self, title, rows, headers):
        print(f"\n{'='*60}")
        print(f"{title}")
        print('='*60)
        if rows:
            print(tabulate(rows, headers=headers, tablefmt='grid'))
        else:
            print("Sin datos disponibles")

    def query_1_precio_promedio_categoria(self):
        query = '''
            SELECT categoria, ROUND(AVG(precio_actual), 2) as precio_promedio
            FROM productos
            WHERE precio_actual IS NOT NULL
            GROUP BY categoria
        '''
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        self.print_result(
            "1. Precio promedio por categoria",
            rows,
            ['Categoria', 'Precio Promedio (MXN)']
        )
        return rows

    def query_2_producto_mas_costoso(self):
        query = '''
            SELECT categoria, nombre, precio_actual
            FROM productos p1
            WHERE precio_actual = (
                SELECT MAX(precio_actual) FROM productos p2 
                WHERE p2.categoria = p1.categoria
            )
        '''
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        self.print_result(
            "2. Producto mas costoso por categoria",
            rows,
            ['Categoria', 'Nombre', 'Precio (MXN)']
        )
        return rows

    def query_3_productos_envio_gratis(self):
        query = '''
            SELECT COUNT(*) as total
            FROM productos
            WHERE envio_gratis = 1
        '''
        self.cursor.execute(query)
        total = self.cursor.fetchone()[0]
        self.cursor.execute('SELECT COUNT(*) FROM productos')
        total_productos = self.cursor.fetchone()[0]
        porcentaje = (total / total_productos * 100) if total_productos > 0 else 0
        print(f"\n{'='*60}")
        print("3. Productos con envio gratis")
        print('='*60)
        print(f"Total: {total} productos ({porcentaje:.1f}% del total)")
        return total

    def query_4_ubicacion_mas_publicaciones(self):
        query = '''
            SELECT ubicacion_vendedor, COUNT(*) as total
            FROM productos
            WHERE ubicacion_vendedor IS NOT NULL AND ubicacion_vendedor != ''
            GROUP BY ubicacion_vendedor
            ORDER BY total DESC
            LIMIT 5
        '''
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        self.print_result(
            "4. Top 5 ubicaciones con mas publicaciones",
            rows,
            ['Ubicacion', 'Total Productos']
        )
        return rows

    def query_5_descuento_promedio_categoria(self):
        query = '''
            SELECT categoria, ROUND(AVG(descuento_porcentaje), 2) as descuento_promedio
            FROM productos
            WHERE precio_anterior IS NOT NULL AND descuento_porcentaje > 0
            GROUP BY categoria
        '''
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        self.print_result(
            "5. Descuento promedio por categoria",
            rows,
            ['Categoria', 'Descuento Promedio (%)']
        )
        return rows

    def query_6_productos_sobre_promedio(self):
        query = '''
            SELECT COUNT(*) as total
            FROM productos
            WHERE precio_actual > (SELECT AVG(precio_actual) FROM productos WHERE precio_actual IS NOT NULL)
        '''
        self.cursor.execute(query)
        total = self.cursor.fetchone()[0]
        self.cursor.execute('SELECT AVG(precio_actual) FROM productos WHERE precio_actual IS NOT NULL')
        promedio = self.cursor.fetchone()[0]
        print(f"\n{'='*60}")
        print("6. Productos por encima del precio promedio general")
        print('='*60)
        print(f"Precio promedio general: ${promedio:,.2f} MXN")
        print(f"Productos sobre el promedio: {total}")
        return total

    def query_7_productos_mas_economicos(self):
        query = '''
            SELECT categoria, nombre, precio_actual
            FROM (
                SELECT *, ROW_NUMBER() OVER(PARTITION BY categoria ORDER BY precio_actual ASC) as rn
                FROM productos 
                WHERE precio_actual IS NOT NULL
            ) 
            WHERE rn <= 5
            ORDER BY categoria, rn
        '''
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        self.print_result(
            "7. 5 productos mas economicos por categoria",
            rows,
            ['Categoria', 'Nombre', 'Precio (MXN)']
        )
        return rows

    def query_8_ahorro_promedio(self):
        query = '''
            SELECT 
                ROUND(AVG(precio_anterior - precio_actual), 2) as ahorro_promedio,
                ROUND(AVG(precio_anterior), 2) as precio_anterior_promedio,
                ROUND(AVG(precio_actual), 2) as precio_actual_promedio
            FROM productos
            WHERE precio_anterior IS NOT NULL AND precio_actual IS NOT NULL
        '''
        self.cursor.execute(query)
        row = self.cursor.fetchone()
        print(f"\n{'='*60}")
        print("8. Ahorro promedio cuando existe precio anterior")
        print('='*60)
        if row and row[0]:
            print(f"Ahorro promedio: ${row[0]:,.2f} MXN")
            print(f"Precio anterior promedio: ${row[1]:,.2f} MXN")
            print(f"Precio actual promedio: ${row[2]:,.2f} MXN")
        else:
            print("No hay productos con precio anterior registrado")
        return row

    def query_9_distribucion_rangos_precio(self):
        query = '''
            SELECT 
                CASE 
                    WHEN precio_actual < 5000 THEN 'Bajo (< $5,000)'
                    WHEN precio_actual BETWEEN 5000 AND 15000 THEN 'Medio ($5,000-$15,000)'
                    ELSE 'Alto (> $15,000)'
                END as rango,
                COUNT(*) as total,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM productos WHERE precio_actual IS NOT NULL), 1) as porcentaje
            FROM productos
            WHERE precio_actual IS NOT NULL
            GROUP BY rango
            ORDER BY 
                CASE rango
                    WHEN 'Bajo (< $5,000)' THEN 1
                    WHEN 'Medio ($5,000-$15,000)' THEN 2
                    ELSE 3
                END
        '''
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        self.print_result(
            "9. Distribucion por rangos de precio",
            rows,
            ['Rango', 'Total', 'Porcentaje (%)']
        )
        return rows

    def run_all_queries(self):
        print("\n" + "="*60)
        print("ANALISIS DE DATOS E-COMMERCE")
        print("="*60)
        self.query_1_precio_promedio_categoria()
        self.query_2_producto_mas_costoso()
        self.query_3_productos_envio_gratis()
        self.query_4_ubicacion_mas_publicaciones()
        self.query_5_descuento_promedio_categoria()
        self.query_6_productos_sobre_promedio()
        self.query_7_productos_mas_economicos()
        self.query_8_ahorro_promedio()
        self.query_9_distribucion_rangos_precio()
        print("\n" + "="*60)
        print("ANALISIS COMPLETADO")
        print("="*60)
