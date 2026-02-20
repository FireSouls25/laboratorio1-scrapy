#!/usr/bin/env python3
import argparse
import os
import sys
import glob
import csv
import subprocess
from datetime import datetime


def run_single_spider(spider_name):
    from scrapy.crawler import CrawlerProcess
    
    os.makedirs('data/raw', exist_ok=True)
    
    settings = {
        'BOT_NAME': 'ecommerce_scraper',
        'SPIDER_MODULES': ['scraper.spiders'],
        'NEWSPIDER_MODULE': 'scraper.spiders',
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'DOWNLOAD_TIMEOUT': 30,
        'COOKIES_ENABLED': False,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8',
        },
        'ITEM_PIPELINES': {
            'scraper.pipelines.ProductosPipeline': 300,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'scraper.middlewares.RandomUserAgentMiddleware': 400,
        },
        'LOG_LEVEL': 'INFO',
        'FEEDS': {
            f'data/raw/{spider_name}.csv': {
                'format': 'csv',
                'encoding': 'utf-8',
                'fields': ['nombre', 'precio_actual', 'precio_anterior', 'descuento_porcentaje', 
                           'ubicacion_vendedor', 'cuotas', 'envio_gratis', 'enlace', 'categoria', 'fecha_extraccion'],
                'overwrite': True,
            }
        }
    }
    
    spider_classes = {
        'laptops': 'scraper.spiders.laptops_spider.LaptopsSpider',
        'celulares': 'scraper.spiders.celulares_spider.CelularesSpider',
        'televisores': 'scraper.spiders.televisores_spider.TelevisoresSpider',
    }
    
    import importlib
    module_path, class_name = spider_classes[spider_name].rsplit('.', 1)
    module = importlib.import_module(module_path)
    spider_class = getattr(module, class_name)
    
    process = CrawlerProcess(settings=settings)
    process.crawl(spider_class)
    process.start()


def run_scrapers():
    print("\n" + "="*60)
    print("FASE 1: EXTRACCION DE DATOS (Web Scraping)")
    print("="*60)
    
    os.makedirs('data/raw', exist_ok=True)
    
    spiders = ['laptops', 'celulares', 'televisores']
    
    for spider_name in spiders:
        print(f"\n--- Ejecutando spider: {spider_name} ---")
        
        result = subprocess.run(
            [sys.executable, __file__, '--spider', spider_name],
            capture_output=False,
            text=True
        )
        
        csv_path = f'data/raw/{spider_name}.csv'
        if os.path.exists(csv_path):
            with open(csv_path, 'r', encoding='utf-8') as f:
                count = sum(1 for _ in csv.DictReader(f))
            print(f"Guardados {count} productos en {csv_path}")
    
    print("\nScraping completado!")


def load_to_database():
    print("\n" + "="*60)
    print("FASE 2: CARGA A BASE DE DATOS")
    print("="*60)
    
    from database.db_manager import DatabaseManager
    
    os.makedirs('database', exist_ok=True)
    
    with DatabaseManager() as db:
        db.create_table()
        print("Tabla 'productos' creada correctamente")
        
        csv_files = sorted(glob.glob('data/raw/*.csv'))
        total_loaded = 0
        
        for csv_file in csv_files:
            if os.path.exists(csv_file):
                count = db.insert_from_csv(csv_file)
                print(f"Cargados {count} productos desde {csv_file}")
                total_loaded += count
        
        total = db.get_total_products()
        print(f"\nTotal de productos en la base de datos: {total}")
        
        if total == 0:
            print("ADVERTENCIA: No se cargaron productos. Verifica los archivos CSV.")


def run_analysis():
    print("\n" + "="*60)
    print("FASE 3: ANALISIS CON SQL")
    print("="*60)
    
    from analysis.queries import AnalysisQueries
    
    with AnalysisQueries() as queries:
        queries.run_all_queries()


def main():
    parser = argparse.ArgumentParser(
        description='Pipeline de Web Scraping E-commerce',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python main.py                  # Ejecuta todo el pipeline
  python main.py --phase scrape   # Solo scraping
  python main.py --phase load     # Solo carga a BD
  python main.py --phase analyze  # Solo analisis
        """
    )
    parser.add_argument(
        '--phase',
        choices=['scrape', 'load', 'analyze'],
        help='Ejecutar solo una fase especifica'
    )
    parser.add_argument(
        '--spider',
        choices=['laptops', 'celulares', 'televisores'],
        help='Ejecutar un spider especifico (uso interno)'
    )
    
    args = parser.parse_args()
    
    if args.spider:
        run_single_spider(args.spider)
    elif args.phase == 'scrape':
        run_scrapers()
    elif args.phase == 'load':
        load_to_database()
    elif args.phase == 'analyze':
        run_analysis()
    else:
        print("\n" + "="*60)
        print("PIPELINE COMPLETO: Web Scraping E-commerce")
        print("="*60)
        run_scrapers()
        load_to_database()
        run_analysis()


if __name__ == '__main__':
    main()
