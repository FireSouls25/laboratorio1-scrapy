import scrapy
from scraper.items import ProductoItem


class LaptopsSpider(scrapy.Spider):
    name = 'laptops'
    allowed_domains = ['mercadolibre.com.mx', 'listado.mercadolibre.com.mx']
    start_urls = ['https://listado.mercadolibre.com.mx/laptops']
    custom_settings = {
        'FEED_URI': 'data/raw/laptops.csv',
    }

    def parse(self, response):
        productos = response.css('li.ui-search-layout__item')
        for producto in productos:
            item = ProductoItem()
            item['nombre'] = self.get_text(producto.css('h2.ui-search-item__title::text'))
            item['precio_actual'] = self.get_text(producto.css('span.andes-money-amount__fraction::text'))
            item['precio_anterior'] = self.get_text(
                producto.css('span.andes-money-amount--previous .andes-money-amount__fraction::text')
            )
            item['ubicacion_vendedor'] = self.get_text(producto.css('span.ui-search-item__location::text'))
            item['cuotas'] = self.get_text(producto.css('span.ui-search-item__group__element.ui-search-installments::text'))
            item['envio_gratis'] = producto.css('span.ui-search-item__shipping--free').get() is not None
            item['enlace'] = producto.css('a.ui-search-link::attr(href)').get()
            item['categoria'] = 'Laptops'
            yield item

        next_page = response.css('a.andes-pagination__link--next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def get_text(self, selector):
        result = selector.get()
        return result.strip() if result else None
