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
    name = 'google_scraper'  # Nom unique pour le spider
    allowed_domains = ['google.com']

    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'LOG_LEVEL': 'INFO',
        'CONCURRENT_REQUESTS_PER_DOMAIN': 5,
        'RETRY_TIMES': 5,
    }

    def start_requests(self):
        # Lire les URLs depuis le fichier CSV
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

        # Extraction du titre principal avec plusieurs sources possibles
        title = sel.xpath("//div[contains(@class, 'PZPZlf') and contains(@class, 'ssJ7i')]/text()").get()
        title_h2 = sel.xpath("//h2[@class='qrShPb pXs6bb PZPZlf q8U8x aTI8gc hNKfZe']/span/text()").get()
        new_title = sel.xpath("//div[@class='PZPZlf ssJ7i B5dxMb' and @data-attrid='title']/text()").get()
        
        final_title = title or title_h2 or new_title  # Combine titles

        # Extraction de l'adresse
        address = sel.xpath("//div[@class='zloOqf PZPZlf']//span[@class='LrzXr']/text()").get()
        address_alt = sel.xpath("//div[contains(@class, 'zloOqf PZPZlf') and contains(@data-dtype, 'd3ifr')]//span[@class='LrzXr']/text()").get()
        final_address = address or address_alt  # Combine addresses

        # Extraction du numéro de téléphone
        phone_number = sel.xpath("//div[@data-local-attribute='d3ph']//span[@aria-label]/text()").get()

        # Extraction des horaires d'ouverture
        hours = {}
        
        # Essayer d'extraire les horaires d'ouverture du premier tableau
        for row in sel.xpath("//tbody/tr"):
            day = row.xpath("td[1]/text()").get()  # Le premier <td> contient le jour
            time_range = row.xpath("td[2]/text()").get()  # Le second <td> contient l'horaire
            
            if day and time_range:
                hours[day.strip().lower()] = time_range.strip()

        # Si aucun horaire n'a été trouvé, essayer d'extraire à partir du second tableau sans classe dans <td>
        if not hours:  # If no hours were found in the first extraction
            for row in sel.xpath("//div[@class='b2JWxc']//table/tbody/tr"):
                day = row.xpath("td[1]/text()").get()  # Le premier <td> contient le jour sans classe
                time_range = row.xpath("td[2]/text()").get()  # Le second <td> contient l'horaire sans classe
                
                if day and time_range:
                    hours[day.strip().lower()] = time_range.strip()

        # Extraction de l'URL du site web
        url = sel.xpath("//a[@class='n1obkb mI8Pwc']/@href").get()

        # Fermer le navigateur Selenium
        driver.quit()

        yield {
            'title': final_title.strip() if final_title else None,
            'address': final_address.strip() if final_address else None,
            'phone': phone_number.strip() if phone_number else None,  # Ajouter le numéro de téléphone au résultat
            'url': url.strip() if url else None, # Inclure l'URL extraite dans le résultat
            'source_url': response.url,  # URL source pour référence
            'hours': hours,  # Ajouter les horaires d'ouverture au résultat sous la clé 'hours'
            # You can add more fields here as needed...
        }
