import scrapy
from scrapy.selector import Selector
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import random

# Middleware pour utiliser un User-Agent aléatoire
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1",
]

class GoogleScraper(scrapy.Spider):
    name = 'google_scraper'
    allowed_domains = ['google.com']

    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'LOG_LEVEL': 'INFO',
        'CONCURRENT_REQUESTS_PER_DOMAIN': 5,
        'RETRY_TIMES': 5,
        'DOWNLOAD_DELAY': 0,  # Pas de délai pour maximiser la vitesse
    }

    def start_requests(self):
        with open('urls.csv', mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                url = row['url'].strip()  # Obtenir l'URL et enlever les espaces
                if url:  # Vérifier que l'URL n'est pas vide
                    yield scrapy.Request(
                        url,
                        callback=self.parse,
                        headers={"User-Agent": random.choice(USER_AGENTS)},
                        dont_filter=True
                    )

    def parse(self, response):
        # Configurer Selenium pour fonctionner en mode headless
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Exécuter Chrome en mode headless
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

        # Ouvrir l'URL dans Selenium
        driver.get(response.url)

        # Attendre que la page soit complètement chargée (ajuster si nécessaire)
        time.sleep(3)

        # Extraire le HTML après le rendu avec Selenium
        sel = Selector(text=driver.page_source)

        # Extraire les données souhaitées
        title = sel.xpath("//div[@class='DoxwDb']//div[@class='PZPZlf ssJ7i B5dxMb']/text()").get()
        address = sel.xpath("//div[@class='zloOqf PZPZlf']//span[@class='LrzXr']/text()").get()
        phone = sel.xpath("//a[@data-dtype='d3ph']//span/text()").get()
        link = sel.xpath("//a[@class='n1obkb mI8Pwc']/@href").get()

        # Fermer le navigateur Selenium
        driver.quit()

        yield {
            'title': title.strip() if title else None,
            'address': address.strip() if address else None,
            'phone': phone.strip() if phone else None,
            'link': link.strip() if link else None,
            'url': response.url
        }