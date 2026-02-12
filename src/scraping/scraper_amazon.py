import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import time
import random
import logging
from pathlib import Path
import sys
from datetime import datetime
import json
from typing import Optional, Dict, List

# --- CONFIGURATION AUTOMATIQUE DES CHEMINS ---
import os

# 1. On cherche d'abord où on est
current_path = Path(__file__).resolve()
project_root = current_path.parent

# 2. On remonte les dossiers jusqu'à trouver 'requirements.txt'
found_root = False
for _ in range(5): 
    if (project_root / "requirements.txt").exists():
        found_root = True
        break
    project_root = project_root.parent

if not found_root:
    print("⚠️ Racine du projet non détectée via le fichier, utilisation du dossier courant.")
    PROJECT_ROOT = Path.cwd()
else:
    PROJECT_ROOT = project_root

DATA_DIR = PROJECT_ROOT / "data" / "raw"
LOGS_DIR = PROJECT_ROOT / "logs"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

print(f"📂 Dossier du projet détecté : {PROJECT_ROOT}")
print(f"📂 Dossier de sauvegarde des données : {DATA_DIR}")

# --- CONFIGURATION LOGGING ---
sys.stdout.reconfigure(encoding='utf-8')
log_file = LOGS_DIR / f"scraper_amazon_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ANTI-DÉTECTION ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
]

class AmazonScraper:
    def __init__(self, headless: bool = False, slow_mo: int = 100):
        self.headless = headless
        self.slow_mo = slow_mo
        self.stats = {
            'total_products': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'pages_scraped': 0
        }
    
    def _get_random_delays(self) -> tuple:
        scroll_delay = random.uniform(1.5, 3.0)
        page_delay = random.uniform(2.5, 5.0)
        action_delay = random.uniform(0.5, 1.5)
        return scroll_delay, page_delay, action_delay
    
    def _clean_price(self, price_text: str) -> Optional[float]:
        if not price_text:
            return None
        try:
            clean = price_text.replace('€', '').replace(' ', '').strip()
            clean = clean.replace(',', '.').replace('\xa0', '')
            return float(clean)
        except ValueError:
            return None
    
    def _extract_rating(self, rating_text: str) -> Optional[float]:
        if not rating_text:
            return None
        try:
            parts = rating_text.split('sur')[0].strip()
            parts = parts.replace(',', '.')
            return float(parts)
        except (ValueError, IndexError):
            return None
    
    def _extract_reviews_count(self, reviews_text: str) -> Optional[int]:
        if not reviews_text:
            return None
        try:
            clean = reviews_text.replace('(', '').replace(')', '').replace(' ', '').replace('\xa0', '')
            return int(clean)
        except ValueError:
            return None
    
    def _extract_product_data(self, card, asin: str) -> Optional[Dict]:
        try:
            product_data = {
                'asin': asin,
                'date_scraping': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'Amazon'
            }
            
            # 1. TITRE
            title = None
            title_selectors = [
                "h2 a span", "h2 span", "a.a-link-normal span.a-text-normal", "a.a-link-normal"
            ]
            for selector in title_selectors:
                if card.locator(selector).count() > 0:
                    title = card.locator(selector).first.inner_text().strip()
                    if title and len(title) > 5:
                        break
            
            if not title:
                return None
            product_data['titre'] = title
            
            # 2. PRIX
            price_raw = None
            if card.locator(".a-price .a-offscreen").count() > 0:
                price_raw = card.locator(".a-price .a-offscreen").first.inner_text()
            product_data['prix_brut'] = price_raw
            product_data['prix'] = self._clean_price(price_raw) if price_raw else None
            
            # 3. NOTE
            rating_raw = None
            if card.locator("i.a-icon-star-small span.a-icon-alt").count() > 0:
                rating_raw = card.locator("i.a-icon-star-small span.a-icon-alt").first.inner_text()
            elif card.locator("span.a-icon-alt").count() > 0:
                rating_raw = card.locator("span.a-icon-alt").first.inner_text()
            product_data['note_brute'] = rating_raw
            product_data['note'] = self._extract_rating(rating_raw) if rating_raw else None
            
            # 4. NOMBRE D'AVIS
            reviews_raw = None
            reviews_selectors = ["span.a-size-base.s-underline-text", "span[aria-label*='étoiles']", "a span.a-size-base"]
            for selector in reviews_selectors:
                if card.locator(selector).count() > 0:
                    text = card.locator(selector).first.inner_text()
                    if text and any(char.isdigit() for char in text):
                        reviews_raw = text
                        break
            product_data['nb_avis_brut'] = reviews_raw
            product_data['nb_avis'] = self._extract_reviews_count(reviews_raw) if reviews_raw else None
            
            # 5. VENDEUR
            seller = None
            if card.locator("span.a-size-base-plus.a-color-base").count() > 0:
                seller = card.locator("span.a-size-base-plus.a-color-base").first.inner_text()
            elif card.locator("h5 span").count() > 0:
                seller_text = card.locator("h5 span").first.inner_text()
                if "Visiter" in seller_text:
                    seller = seller_text.replace("Visiter la boutique ", "").strip()
            product_data['vendeur'] = seller
            
            # 6. BADGE PRIME
            is_prime = card.locator("i.a-icon-prime").count() > 0
            product_data['prime'] = is_prime
            
            # 7. DISPONIBILITÉ
            availability = "En stock"
            if card.locator("span.a-color-price").count() > 0:
                avail_text = card.locator("span.a-color-price").first.inner_text()
                if "rupture" in avail_text.lower() or "indisponible" in avail_text.lower():
                    availability = "Rupture de stock"
            product_data['disponibilite'] = availability
            
            # 8. LIEN & IMAGE
            product_data['lien'] = f"https://www.amazon.fr/dp/{asin}"
            image_url = None
            if card.locator("img.s-image").count() > 0:
                image_url = card.locator("img.s-image").first.get_attribute("src")
            product_data['image_url'] = image_url
            
            # Validation finale
            if title and (product_data['prix'] is not None or product_data['note'] is not None):
                self.stats['successful_extractions'] += 1
                return product_data
            else:
                return None
                
        except Exception as e:
            logger.error(f"Erreur extraction ASIN {asin}: {str(e)}")
            self.stats['failed_extractions'] += 1
            return None
    
    def _handle_cookies_banner(self, page):
        try:
            if page.locator("#sp-cc-accept").is_visible(timeout=3000):
                page.click("#sp-cc-accept")
                logger.info("🍪 Cookies acceptés")
                time.sleep(1)
        except:
            pass
    
    def _smart_scroll(self, page):
        """
        Scroll intelligent CORRIGÉ.
        Vérifie que la page est bien chargée avant de scroller pour éviter le crash.
        """
        try:
            # Attendre que le body de la page existe
            page.wait_for_selector("body", timeout=5000)
            
            scroll_delay, _, _ = self._get_random_delays()
            
            # Vérification supplémentaire : le body est-il accessible ?
            body_exists = page.evaluate("() => document.body")
            
            if body_exists:
                # Scroll moitié
                page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2);")
                time.sleep(scroll_delay)
                
                # Scroll bas
                page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_delay)
                
                # Petit remontée
                page.evaluate("window.scrollBy(0, -300);")
                time.sleep(0.5)
            else:
                logger.warning("⚠️ Corps de page introuvable (probablement un CAPTCHA). Scroll ignoré.")
                
        except Exception as e:
            logger.warning(f"Erreur lors du scroll : {e}")
    
    def scrape(self, keyword: str, max_pages: int = 1, save_json: bool = False) -> pd.DataFrame:
        logger.info(f"🚀 Démarrage scraping Amazon : '{keyword}' ({max_pages} pages)")
        products = []
        
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(
                    headless=self.headless,
                    slow_mo=self.slow_mo,
                    args=['--disable-blink-features=AutomationControlled', '--disable-dev-shm-usage']
                )
                
                context = browser.new_context(
                    user_agent=random.choice(USER_AGENTS),
                    viewport={'width': 1920, 'height': 1080},
                    locale='fr-FR',
                    timezone_id='Europe/Paris'
                )
                
                context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
                page = context.new_page()
                
                base_url = f"https://www.amazon.fr/s?k={keyword.replace(' ', '+')}"
                logger.info(f"🌍 Connexion à {base_url}")
                
                page.goto(base_url, timeout=60000, wait_until='domcontentloaded')
                self._handle_cookies_banner(page)
                
                for current_page in range(1, max_pages + 1):
                    logger.info(f"📄 Page {current_page}/{max_pages}")
                    self.stats['pages_scraped'] += 1
                    
                    self._smart_scroll(page)
                    
                    try:
                        page.wait_for_selector('div[data-asin]:not([data-asin=""])', timeout=10000)
                    except PlaywrightTimeout:
                        logger.error("Timeout : Produits non chargés (ou CAPTCHA)")
                        break
                    
                    cards = page.locator('div[data-asin]:not([data-asin=""])').all()
                    logger.info(f"   📦 {len(cards)} cartes produits détectées")
                    
                    for idx, card in enumerate(cards, 1):
                        try:
                            asin = card.get_attribute("data-asin")
                            if not asin or len(asin) != 10:
                                continue
                            
                            product = self._extract_product_data(card, asin)
                            if product:
                                products.append(product)
                                if idx % 10 == 0:
                                    logger.info(f"   ✓ {idx}/{len(cards)} produits traités")
                        
                        except Exception as e:
                            logger.error(f"   ⚠️ Erreur produit #{idx}: {str(e)}")
                            continue
                    
                    self.stats['total_products'] = len(products)
                    logger.info(f"   💾 Total accumulé : {len(products)} produits")
                    
                    if current_page < max_pages:
                        try:
                            _, page_delay, _ = self._get_random_delays()
                            next_btn = page.locator("a.s-pagination-next")
                            if next_btn.is_visible() and next_btn.is_enabled():
                                logger.info(f"➡️  Page {current_page + 1}...")
                                next_btn.click()
                                time.sleep(page_delay)
                            else:
                                logger.warning("🛑 Bouton 'Suivant' introuvable")
                                break
                        except Exception as e:
                            logger.error(f"Erreur pagination : {e}")
                            break
                
                browser.close()
                logger.info("🔒 Navigateur fermé")
            
            except Exception as e:
                logger.error(f"❌ Erreur critique : {str(e)}")
                return pd.DataFrame()
        
        return self._save_data(products, keyword, save_json)
    
    def _save_data(self, products: List[Dict], keyword: str, save_json: bool) -> pd.DataFrame:
        if not products:
            logger.warning("❌ Aucun produit récupéré")
            self._print_stats()
            return pd.DataFrame()
        
        df = pd.DataFrame(products)
        column_order = [
            'date_scraping', 'asin', 'titre', 'prix', 'prix_brut',
            'note', 'note_brute', 'nb_avis', 'nb_avis_brut',
            'vendeur', 'prime', 'disponibilite', 'lien', 'image_url', 'source'
        ]
        df = df[[col for col in column_order if col in df.columns]]
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_keyword = keyword.replace(' ', '_').replace('/', '_')
        
        csv_filename = f"amazon_{safe_keyword}_{timestamp}.csv"
        csv_path = DATA_DIR / csv_filename
        df.to_csv(csv_path, index=False, encoding='utf-8')
        logger.info(f"✅ CSV sauvegardé : {csv_path}")
        
        if save_json:
            json_data = {
                'metadata': {'keyword': keyword, 'scraping_date': timestamp, 'total_products': len(df)},
                'products': products
            }
            json_path = DATA_DIR / f"amazon_{safe_keyword}_{timestamp}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        self._print_stats()
        return df
    
    def _print_stats(self):
        logger.info("\n" + "="*60)
        logger.info("📊 STATISTIQUES DU SCRAPING")
        logger.info("="*60)
        logger.info(f"Pages scrapées       : {self.stats['pages_scraped']}")
        logger.info(f"Produits trouvés     : {self.stats['total_products']}")
        logger.info(f"Extractions réussies : {self.stats['successful_extractions']}")
        logger.info(f"Extractions échouées : {self.stats['failed_extractions']}")
        logger.info("="*60 + "\n")

def main():
    # ⚠️ headless=False pour voir si un CAPTCHA apparaît
    scraper = AmazonScraper(headless=False, slow_mo=100)
    
    keywords = ["smartphone", "iphone", "samsung galaxy", "android Smartphone", "xiaomi"]
    all_dfs = []

    for keyword in keywords:
        print(f"\n🚀 Lancement du scraping pour : {keyword}")
        # On limite à 5  pages par mot-clé pour commencer 
        df = scraper.scrape(keyword, max_pages=5, save_json=False)
        
        if not df.empty:
            print(f"✅ {len(df)} produits récupérés pour '{keyword}'")
            all_dfs.append(df)
        else:
            print(f"⚠️ Aucun produit pour '{keyword}'")
    
    if all_dfs:
        final_df = pd.concat(all_dfs, ignore_index=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = DATA_DIR / f"amazon_global_{timestamp}.csv"
        final_df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"\n✅ TERMINÉ ! Total de produits récupérés : {len(final_df)}")
        print(f"📁 Fichier sauvegardé : {output_path}")
    else:
        print("❌ Aucun produit récupéré.")

if __name__ == "__main__":
    main()