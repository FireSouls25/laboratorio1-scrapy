import sqlite3
import os
from pathlib import Path


class DatabaseManager:
    def __init__(self, db_path='database/ecommerce.db'):
        self.db_path = db_path
        Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.cursor = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        return self

    def close(self):
        if self.conn:
            self.conn.close()

    def create_table(self):
        self.cursor.executescript('''
            DROP TABLE IF EXISTS productos;
            
            CREATE TABLE productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                precio_actual REAL,
                precio_anterior REAL,
                descuento_porcentaje INTEGER DEFAULT 0,
                ubicacion_vendedor TEXT,
                cuotas INTEGER DEFAULT 0,
                envio_gratis INTEGER DEFAULT 0,
                enlace TEXT UNIQUE,
                categoria TEXT NOT NULL,
                fecha_extraccion TEXT NOT NULL
            );
            
            CREATE INDEX IF NOT EXISTS idx_categoria ON productos(categoria);
            CREATE INDEX IF NOT EXISTS idx_precio ON productos(precio_actual);
            CREATE INDEX IF NOT EXISTS idx_ubicacion ON productos(ubicacion_vendedor);
        ''')
        self.conn.commit()

    def insert_product(self, producto):
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO productos 
                (nombre, precio_actual, precio_anterior, descuento_porcentaje,
                 ubicacion_vendedor, cuotas, envio_gratis, enlace, categoria, fecha_extraccion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                producto.get('nombre'),
                producto.get('precio_actual'),
                producto.get('precio_anterior'),
                producto.get('descuento_porcentaje', 0),
                producto.get('ubicacion_vendedor'),
                producto.get('cuotas', 0),
                producto.get('envio_gratis', 0),
                producto.get('enlace'),
                producto.get('categoria'),
                producto.get('fecha_extraccion')
            ))
            return True
        except sqlite3.IntegrityError:
            return False

    def insert_from_csv(self, csv_path):
        import csv
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                if self.insert_product(row):
                    count += 1
            self.conn.commit()
        return count

    def get_total_products(self):
        self.cursor.execute('SELECT COUNT(*) FROM productos')
        return self.cursor.fetchone()[0]

    def __enter__(self):
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
