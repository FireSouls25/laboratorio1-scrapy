import re
from datetime import datetime
from scraper.items import ProductoItem


class ProductosPipeline:
    def process_item(self, item, spider):
        if isinstance(item, ProductoItem):
            item['precio_actual'] = self.parse_precio(item.get('precio_actual'))
            item['precio_anterior'] = self.parse_precio(item.get('precio_anterior'))
            item['descuento_porcentaje'] = self.calcular_descuento(
                item.get('precio_actual'),
                item.get('precio_anterior')
            )
            item['cuotas'] = self.parse_cuotas(item.get('cuotas'))
            item['envio_gratis'] = 1 if item.get('envio_gratis') else 0
            item['fecha_extraccion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if item.get('nombre'):
                item['nombre'] = item['nombre'].strip()
            if item.get('ubicacion_vendedor'):
                item['ubicacion_vendedor'] = item['ubicacion_vendedor'].strip()
        return item

    def parse_precio(self, valor):
        if valor is None:
            return None
        if isinstance(valor, (int, float)):
            return float(valor)
        valor_str = str(valor)
        valor_limpio = re.sub(r'[^\d.]', '', valor_str)
        try:
            return float(valor_limpio) if valor_limpio else None
        except ValueError:
            return None

    def calcular_descuento(self, precio_actual, precio_anterior):
        if precio_actual and precio_anterior and precio_anterior > 0:
            descuento = ((precio_anterior - precio_actual) / precio_anterior) * 100
            return int(round(descuento))
        return 0

    def parse_cuotas(self, valor):
        if valor is None:
            return 0
        if isinstance(valor, int):
            return valor
        valor_str = str(valor)
        match = re.search(r'(\d+)', valor_str)
        return int(match.group(1)) if match else 0
