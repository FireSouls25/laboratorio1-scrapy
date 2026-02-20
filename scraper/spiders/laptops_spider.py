import scrapy
from scraper.items import ProductoItem
import re


class LaptopsSpider(scrapy.Spider):
    name = 'laptops'
    allowed_domains = ['mercadolibre.com.mx', 'listado.mercadolibre.com.mx']
    start_urls = ['https://listado.mercadolibre.com.mx/laptops']
    custom_settings = {
        'FEEDS': {
            'data/raw/laptops.csv': {
                'format': 'csv',
                'encoding': 'utf-8',
                'fields': ['nombre', 'precio_actual', 'precio_anterior', 'descuento_porcentaje', 
                           'ubicacion_vendedor', 'cuotas', 'envio_gratis', 'enlace', 'categoria', 'fecha_extraccion'],
            }
        }
    }

    def parse(self, response):
        productos = response.css('li.ui-search-layout__item')
        
        for producto in productos:
            item = ProductoItem()
            
            item['nombre'] = producto.css('a.poly-component__title::text').get()
            
            precio_current = producto.css('.poly-price__current .andes-money-amount__fraction::text').get()
            item['precio_actual'] = self.parse_precio(precio_current)
            
            precio_original = producto.css('.andes-money-amount--previous .andes-money-amount__fraction::text').get()
            item['precio_anterior'] = self.parse_precio(precio_original)
            
            descuento_text = producto.css('span.andes-money-amount__discount::text').get()
            item['descuento_porcentaje'] = self.parse_descuento(descuento_text)
            
            ubicacion = producto.css('.poly-component__shipped-from::text').get()
            item['ubicacion_vendedor'] = ubicacion.strip() if ubicacion else None
            
            cuotas_text = producto.css('span.poly-price__installments::text').get()
            item['cuotas'] = self.parse_cuotas(cuotas_text)
            
            shipping_text = producto.css('.poly-component__shipping::text').get() or ''
            item['envio_gratis'] = 'Envío gratis' in shipping_text
            
            enlace = producto.css('a.poly-component__title::attr(href)').get()
            if enlace and '#' in enlace:
                enlace = enlace.split('#')[0]
            item['enlace'] = enlace
            
            item['categoria'] = 'Laptops'
            yield item

        next_page = response.css('a.andes-pagination__link--next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_precio(self, texto):
        if not texto:
            return None
        limpio = texto.replace(',', '').replace('.', '').strip()
        try:
            return float(limpio)
        except ValueError:
            return None

    def parse_descuento(self, texto):
        if not texto:
            return 0
        match = re.search(r'(\d+)', texto)
        return int(match.group(1)) if match else 0

    def parse_cuotas(self, texto):
        if not texto:
            return 0
        match = re.search(r'(\d+)\s*meses', texto)
        return int(match.group(1)) if match else 0
