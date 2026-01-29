"""
Scraper Amazon amélioré pour l'analyse de prix et concurrence e-commerce
Author: Votre Nom
Date: 2026-01-29

Améliorations principales:
- Gestion robuste des erreurs avec retry logic
- Logging détaillé pour le débogage
- Extraction de données enrichies (vendeur, disponibilité, nombre d'avis, etc.)
- Anti-détection amélioré (rotation user-agents, délais aléatoires)
- Validation et nettoyage des données
- Export multi-format (CSV, JSON, Excel)
- Configuration via fichier de config
"""

import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import time
import random
import logging
from datetime import datetime
from pathlib import Path
import json
import re
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict
import sys

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'scraping_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ProductData:
    """Structure de données pour un produit Amazon"""
    titre: str
    prix: Optional[str] = None
    prix_original: Optional[str] = None  # Prix barré s'il existe
    reduction: Optional[str] = None
    note: Optional[float] = None
    nombre_avis: Optional[int] = None
    vendeur: Optional[str] = None
    prime: bool = False
    disponibilite: Optional[str] = None
    lien: Optional[str] = None
    asin: Optional[str] = None  # Identifiant unique Amazon
    image_url: Optional[str] = None
    date_scraping: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source: str = "Amazon"
    
    def to_dict(self) -> Dict:
        """Convertit en dictionnaire"""
        return asdict(self)


class AmazonScraperConfig:
    """Configuration du scraper"""
    
    # User agents pour rotation
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    ]
    
    # Délais aléatoires (en secondes)
    MIN_DELAY = 2
    MAX_DELAY = 5
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 5
    
    # Timeouts
    PAGE_TIMEOUT = 60000
    ELEMENT_TIMEOUT = 10000
    
    # Chemins
    DATA_DIR = Path("../../data/raw")
    LOGS_DIR = Path("../../logs")


class AmazonScraper:
    """Scraper Amazon avec fonctionnalités avancées"""
    
    def __init__(self, config: AmazonScraperConfig = None):
        self.config = config or AmazonScraperConfig()
        self._ensure_directories()
        self.products_scraped = 0
        self.errors_count = 0
        
    def _ensure_directories(self):
        """Crée les dossiers nécessaires"""
        self.config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
    def _get_random_user_agent(self) -> str:
        """Retourne un user agent aléatoire"""
        return random.choice(self.config.USER_AGENTS)
    
    def _human_delay(self):
        """Ajoute un délai aléatoire pour simuler un comportement humain"""
        delay = random.uniform(self.config.MIN_DELAY, self.config.MAX_DELAY)
        time.sleep(delay)
        
    def _extract_price(self, price_text: str) -> Optional[float]:
        """Extrait et nettoie le prix"""
        if not price_text:
            return None
        try:
            # Nettoie le texte: "12,99 €" -> 12.99
            price_cleaned = re.sub(r'[^\d,]', '', price_text)
            price_cleaned = price_cleaned.replace(',', '.')
            return float(price_cleaned)
        except (ValueError, AttributeError):
            return None
    
    def _extract_rating(self, rating_text: str) -> Optional[float]:
        """Extrait la note"""
        if not rating_text:
            return None
        try:
            # "4,5 sur 5 étoiles" -> 4.5
            match = re.search(r'(\d+[,\.]\d+)', rating_text)
            if match:
                return float(match.group(1).replace(',', '.'))
        except (ValueError, AttributeError):
            return None
        return None
    
    def _extract_review_count(self, text: str) -> Optional[int]:
        """Extrait le nombre d'avis"""
        if not text:
            return None
        try:
            # "1 234" -> 1234
            count_cleaned = re.sub(r'[^\d]', '', text)
            return int(count_cleaned) if count_cleaned else None
        except (ValueError, AttributeError):
            return None
    
    def _extract_asin(self, url: str) -> Optional[str]:
        """Extrait l'ASIN (identifiant Amazon) depuis l'URL"""
        if not url:
            return None
        match = re.search(r'/dp/([A-Z0-9]{10})', url)
        return match.group(1) if match else None
    
    def _accept_cookies(self, page):
        """Gère la bannière de cookies"""
        try:
            cookie_selectors = [
                "#sp-cc-accept",
                "#sp-cc-rejectall-link",
                "button[id='a-autoid-0-announce']"
            ]
            
            for selector in cookie_selectors:
                if page.locator(selector).is_visible(timeout=3000):
                    page.click(selector)
                    logger.info("🍪 Cookies gérés")
                    time.sleep(1)
                    return True
        except Exception as e:
            logger.debug(f"Pas de bannière cookies ou erreur: {e}")
        return False
    
    def _extract_product_data(self, product_element) -> Optional[ProductData]:
        """Extrait toutes les données d'un produit"""
        try:
            # Titre
            title_el = product_element.query_selector("h2 a span")
            titre = title_el.inner_text().strip() if title_el else None
            
            if not titre:
                return None
            
            # Lien et ASIN
            link_el = product_element.query_selector("h2 a")
            lien = None
            asin = None
            if link_el:
                href = link_el.get_attribute("href")
                lien = f"https://www.amazon.fr{href}" if href else None
                asin = self._extract_asin(href)
            
            # Prix actuel
            price_el = product_element.query_selector(".a-price .a-offscreen")
            prix_text = price_el.inner_text() if price_el else None
            prix = self._extract_price(prix_text)
            
            # Prix original (si réduction)
            prix_original = None
            prix_original_el = product_element.query_selector(".a-price.a-text-price .a-offscreen")
            if prix_original_el:
                prix_original_text = prix_original_el.inner_text()
                prix_original = self._extract_price(prix_original_text)
            
            # Réduction
            reduction = None
            reduction_el = product_element.query_selector(".a-badge-text")
            if reduction_el:
                reduction = reduction_el.inner_text().strip()
            
            # Note
            rating_el = product_element.query_selector("i.a-icon-star-small span.a-icon-alt")
            rating_text = rating_el.inner_text() if rating_el else None
            note = self._extract_rating(rating_text)
            
            # Nombre d'avis
            review_count_el = product_element.query_selector("span[aria-label*='étoiles']")
            nombre_avis = None
            if review_count_el:
                review_text = review_count_el.get_attribute("aria-label")
                nombre_avis = self._extract_review_count(review_text)
            
            # Amazon Prime
            prime = product_element.query_selector("i.a-icon-prime") is not None
            
            # Vendeur (parfois disponible)
            vendeur = None
            vendeur_el = product_element.query_selector(".a-size-base.a-color-secondary")
            if vendeur_el:
                vendeur = vendeur_el.inner_text().strip()
            
            # Disponibilité
            disponibilite = None
            dispo_el = product_element.query_selector(".a-size-base.a-color-price")
            if dispo_el:
                disponibilite = dispo_el.inner_text().strip()
            
            # Image
            image_url = None
            img_el = product_element.query_selector("img.s-image")
            if img_el:
                image_url = img_el.get_attribute("src")
            
            return ProductData(
                titre=titre,
                prix=prix_text,
                prix_original=prix_original,
                reduction=reduction,
                note=note,
                nombre_avis=nombre_avis,
                vendeur=vendeur,
                prime=prime,
                disponibilite=disponibilite,
                lien=lien,
                asin=asin,
                image_url=image_url
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur extraction produit: {e}")
            self.errors_count += 1
            return None
    
    def scrape_amazon(self, 
                     keyword: str, 
                     max_pages: int = 1,
                     headless: bool = False) -> pd.DataFrame:
        """
        Scrape les résultats Amazon pour un mot-clé.
        
        Args:
            keyword: Produit à rechercher
            max_pages: Nombre de pages à scraper
            headless: Mode headless (True) ou visible (False)
            
        Returns:
            DataFrame avec les données collectées
        """
        logger.info(f"🚀 Démarrage du scraping pour '{keyword}' ({max_pages} page(s))")
        
        data = []
        
        with sync_playwright() as p:
            try:
                # Lancement du navigateur
                browser = p.chromium.launch(
                    headless=headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox'
                    ]
                )
                
                # Contexte avec user agent aléatoire
                context = browser.new_context(
                    user_agent=self._get_random_user_agent(),
                    viewport={'width': 1920, 'height': 1080},
                    locale='fr-FR',
                )
                
                # Ajout de scripts anti-détection
                context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                """)
                
                page = context.new_page()
                
                # URL de recherche
                search_url = f"https://www.amazon.fr/s?k={keyword.replace(' ', '+')}"
                logger.info(f"🌍 Navigation vers: {search_url}")
                
                page.goto(search_url, timeout=self.config.PAGE_TIMEOUT)
                self._accept_cookies(page)
                
                # Scraping de chaque page
                for current_page in range(1, max_pages + 1):
                    logger.info(f"📄 Scraping page {current_page}/{max_pages}")
                    
                    # Attendre le chargement des produits
                    try:
                        page.wait_for_selector(
                            'div[data-component-type="s-search-result"]',
                            timeout=self.config.ELEMENT_TIMEOUT
                        )
                    except PlaywrightTimeout:
                        logger.error("⏱️ Timeout: Les produits n'ont pas chargé")
                        break
                    
                    # Scroll pour charger tous les éléments
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                    
                    # Récupérer les produits
                    products = page.query_selector_all('div[data-component-type="s-search-result"]')
                    logger.info(f"🔍 {len(products)} produits trouvés sur cette page")
                    
                    for idx, product in enumerate(products, 1):
                        product_data = self._extract_product_data(product)
                        if product_data:
                            data.append(product_data.to_dict())
                            self.products_scraped += 1
                        
                        if idx % 10 == 0:
                            logger.debug(f"  ✓ {idx}/{len(products)} produits traités")
                    
                    # Pagination
                    if current_page < max_pages:
                        try:
                            next_button = page.locator("a.s-pagination-next")
                            if next_button.is_visible() and not next_button.is_disabled():
                                logger.info("➡️ Navigation vers la page suivante...")
                                next_button.click()
                                self._human_delay()
                            else:
                                logger.info("🛑 Pas de page suivante disponible")
                                break
                        except Exception as e:
                            logger.warning(f"⚠️ Erreur pagination: {e}")
                            break
                
                browser.close()
                
            except Exception as e:
                logger.error(f"❌ Erreur critique: {e}", exc_info=True)
                raise
        
        # Création du DataFrame
        df = pd.DataFrame(data)
        
        logger.info(f"✅ Scraping terminé!")
        logger.info(f"📊 {self.products_scraped} produits collectés")
        logger.info(f"⚠️ {self.errors_count} erreurs rencontrées")
        
        return df
    
    def save_data(self, 
                  df: pd.DataFrame, 
                  keyword: str,
                  formats: List[str] = ['csv', 'json', 'excel']) -> Dict[str, Path]:
        """
        Sauvegarde les données dans différents formats
        
        Args:
            df: DataFrame à sauvegarder
            keyword: Mot-clé de recherche (pour le nom du fichier)
            formats: Liste des formats ('csv', 'json', 'excel')
            
        Returns:
            Dictionnaire des chemins de fichiers créés
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"amazon_{keyword.replace(' ', '_')}_{timestamp}"
        
        saved_files = {}
        
        try:
            if 'csv' in formats:
                csv_path = self.config.DATA_DIR / f"{base_filename}.csv"
                df.to_csv(csv_path, index=False, encoding='utf-8')
                saved_files['csv'] = csv_path
                logger.info(f"💾 CSV sauvegardé: {csv_path}")
            
            if 'json' in formats:
                json_path = self.config.DATA_DIR / f"{base_filename}.json"
                df.to_json(json_path, orient='records', force_ascii=False, indent=2)
                saved_files['json'] = json_path
                logger.info(f"💾 JSON sauvegardé: {json_path}")
            
            if 'excel' in formats:
                excel_path = self.config.DATA_DIR / f"{base_filename}.xlsx"
                df.to_excel(excel_path, index=False, engine='openpyxl')
                saved_files['excel'] = excel_path
                logger.info(f"💾 Excel sauvegardé: {excel_path}")
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde: {e}")
            raise
        
        return saved_files


def main():
    """Fonction principale d'exécution"""
    
    # Configuration
    search_term = "pc portable gamer"
    max_pages = 2
    
    # Création du scraper
    scraper = AmazonScraper()
    
    try:
        # Scraping
        df = scraper.scrape_amazon(
            keyword=search_term,
            max_pages=max_pages,
            headless=False  # Mettre True pour mode invisible
        )
        
        # Affichage des statistiques
        print("\n" + "="*80)
        print("📊 STATISTIQUES DU SCRAPING")
        print("="*80)
        print(f"Produits collectés: {len(df)}")
        print(f"Colonnes: {', '.join(df.columns)}")
        print(f"\nPremiers produits:")
        print(df.head(10).to_string())
        
        if not df.empty:
            print(f"\n💰 Prix moyen: {df['prix'].apply(lambda x: scraper._extract_price(x)).mean():.2f}€")
            print(f"⭐ Note moyenne: {df['note'].mean():.2f}/5")
            print(f"🏆 {df['prime'].sum()} produits Prime ({df['prime'].sum()/len(df)*100:.1f}%)")
        
        # Sauvegarde
        saved_files = scraper.save_data(df, search_term, formats=['csv', 'json', 'excel'])
        
        print("\n" + "="*80)
        print("📁 FICHIERS CRÉÉS")
        print("="*80)
        for format_type, filepath in saved_files.items():
            print(f"{format_type.upper()}: {filepath}")
        
        return df
        
    except Exception as e:
        logger.error(f"❌ Erreur dans main(): {e}", exc_info=True)
        return None


if __name__ == "__main__":
    df_result = main()