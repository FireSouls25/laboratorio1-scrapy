#!/usr/bin/env python3
import argparse
import os
import sys
import glob
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def run_scrapers():
    print("\n" + "="*60)
    print("FASE 1: EXTRACCION DE DATOS (Web Scraping)")
    print("="*60)
    
    os.environ['SCRAPY_SETTINGS_MODULE'] = 'scraper.settings'
    
    process = CrawlerProcess(settings={
        'BOT_NAME': 'ecommerce_scraper',
        'SPIDER_MODULES': ['scraper.spiders'],
        'NEWSPIDER_MODULE': 'scraper.spiders',
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2,
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
        'FEED_FORMAT': 'csv',
        'FEED_EXPORT_ENCODING': 'utf-8',
    })
    
    from scraper.spiders.laptops_spider import LaptopsSpider
    from scraper.spiders.celulares_spider import CelularesSpider
    from scraper.spiders.televisores_spider import TelevisoresSpider
    
    spiders = [
        ('laptops', LaptopsSpider, 'data/raw/laptops.csv'),
        ('celulares', CelularesSpider, 'data/raw/celulares.csv'),
        ('televisores', TelevisoresSpider, 'data/raw/televisores.csv'),
    ]
    
    os.makedirs('data/raw', exist_ok=True)
    
    for name, spider_class, output_path in spiders:
        print(f"\n--- Ejecutando spider: {name} ---")
        process.crawl(spider_class)
    
    process.start()
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
        
        csv_files = glob.glob('data/raw/*.csv')
        total_loaded = 0
        
        for csv_file in csv_files:
            if os.path.exists(csv_file):
                count = db.insert_from_csv(csv_file)
                print(f"Cargados {count} productos desde {csv_file}")
                total_loaded += count
        
        print(f"\nTotal de productos en la base de datos: {db.get_total_products()}")


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
    
    args = parser.parse_args()
    
    if args.phase == 'scrape':
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
