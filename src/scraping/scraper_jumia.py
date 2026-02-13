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
import os

# --- CONFIGURATION AUTOMATIQUE DES CHEMINS (VERSION BLINDÉE) ---
current_path = Path(__file__).resolve()
project_root = current_path.parent
found_root = False
for _ in range(5):
    if (project_root / "requirements.txt").exists():
        found_root = True
        break
    project_root = project_root.parent

if not found_root:
    PROJECT_ROOT = Path.cwd()
else:
    PROJECT_ROOT = project_root

DATA_DIR = PROJECT_ROOT / "data" / "raw"
LOGS_DIR = PROJECT_ROOT / "logs"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# --- CONFIGURATION LOGGING ---
sys.stdout.reconfigure(encoding='utf-8')
log_file = LOGS_DIR / f"scraper_jumia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class JumiaScraper:
    """
    Scraper Jumia professionnel.
    Structure identique au scraper Amazon pour faciliter la fusion des données.
    """
    
    def __init__(self, headless: bool = False, slow_mo: int = 50):
        self.headless = headless
        self.slow_mo = slow_mo
        self.stats = {
            'total_products': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'pages_scraped': 0
        }
    
    def _get_random_delays(self) -> tuple:
        """Génère des délais aléatoires"""
        scroll_delay = random.uniform(1.5, 3.0)
        return scroll_delay
    
    def _clean_price(self, price_text: str) -> Optional[float]:
        """Convertit '1 500.00 Dhs' en 1500.00"""
        if not price_text:
            return None
        try:
            # Nettoyage spécifique Jumia (Dhs, espaces)
            clean = price_text.upper().replace('DHS', '').replace('DH', '').replace(',', '.')
            clean = clean.replace(' ', '').strip()
            return float(clean)
        except ValueError:
            return None

    def _extract_rating(self, rating_text: str) -> Optional[float]:
        """Convertit '4.5 out of 5' en 4.5"""
        if not rating_text:
            return None
        try:
            return float(rating_text.split('out')[0].strip())
        except:
            return None

    def _handle_popup(self, page):
        """Ferme la pop-up Newsletter de Jumia si elle apparaît"""
        try:
            popup_closers = [
                "button[aria-label='newsletter_popup_close-cta']",
                "#pop button.cls",
                ".newsletter_popup .close"
            ]
            
            for selector in popup_closers:
                if page.locator(selector).is_visible(timeout=2000):
                    logger.info("🧹 Fermeture de la pop-up Jumia...")
                    page.click(selector)
                    time.sleep(1)
                    break
        except:
            pass

    def _smart_scroll(self, page):
        """
        Scroll intelligent sécurisé (Identique à Amazon)
        """
        try:
            page.wait_for_selector("body", timeout=5000)
            scroll_delay = self._get_random_delays()
            
            body_exists = page.evaluate("() => document.body")
            if body_exists:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2);")
                time.sleep(scroll_delay)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_delay)
        except Exception as e:
            logger.warning(f"Erreur scroll Jumia : {e}")

    def scrape(self, keyword: str, max_pages: int = 1) -> pd.DataFrame:
        logger.info(f"🚀 Démarrage scraping Jumia : '{keyword}'")
        products = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless, slow_mo=self.slow_mo)
            page = browser.new_page()
            
            base_url = f"https://www.jumia.ma/catalog/?q={keyword.replace(' ', '+')}"
            logger.info(f"🌍 Connexion à {base_url}")
            page.goto(base_url, timeout=60000)
            
            self._handle_popup(page)
            
            for current_page in range(1, max_pages + 1):
                logger.info(f"📄 Page {current_page}/{max_pages}")
                self.stats['pages_scraped'] += 1
                
                # Scroll sécurisé
                self._smart_scroll(page)
                time.sleep(1) # Pause supplémentaire pour Jumia qui est parfois lent à charger les images
                
                # Sélecteurs Jumia
                cards = page.locator("article.prd._fb.col.c-prd").all()
                if not cards:
                    cards = page.locator("article.prd").all()
                
                logger.info(f"   📦 {len(cards)} produits détectés")
                
                for card in cards:
                    try:
                        # Lien & ID
                        link_el = card.locator("a.core")
                        if not link_el.count(): continue
                        
                        relative_link = link_el.get_attribute("href")
                        full_link = f"https://www.jumia.ma{relative_link}"
                        data_id = card.get_attribute("data-id") or relative_link
                        
                        # Titre
                        title = "Inconnu"
                        if card.locator("h3.name").count():
                            title = card.locator("h3.name").first.inner_text()
                        
                        # Prix
                        price_raw = None
                        if card.locator("div.prc").count():
                            price_raw = card.locator("div.prc").first.inner_text()
                            
                        # Note
                        rating_raw = None
                        if card.locator("div.stars._s").count():
                            rating_raw = card.locator("div.stars._s").first.inner_text()
                        
                        # Nettoyage
                        price = self._clean_price(price_raw)
                        rating = self._extract_rating(rating_raw)
                        
                        # On garde le produit si on a un titre et un prix
                        if title != "Inconnu" and price:
                            products.append({
                                "date_scraping": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                "source": "Jumia",
                                "titre": title,
                                "prix": price,
                                "prix_brut": price_raw,
                                "note": rating,
                                "nb_avis": 0, # Jumia n'affiche pas le nb d'avis sur la liste facilement
                                "lien": full_link,
                                "id_produit": data_id
                            })
                            self.stats['successful_extractions'] += 1
                            
                    except Exception as e:
                        self.stats['failed_extractions'] += 1
                        continue
                
                # Pagination
                if current_page < max_pages:
                    next_btn = page.locator("a[aria-label='Page suivante']")
                    if next_btn.is_visible():
                        logger.info("➡️ Page suivante...")
                        next_btn.click()
                        time.sleep(3)
                    else:
                        logger.info("🛑 Fin de pagination")
                        break
            
            browser.close()

        # Sauvegarde individuelle par mot-clé
        if products:
            df = pd.DataFrame(products)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_keyword = keyword.replace(' ', '_')
            filename = f"jumia_{safe_keyword}_{timestamp}.csv"
            output_path = DATA_DIR / filename
            
            df.to_csv(output_path, index=False, encoding='utf-8')
            logger.info(f"✅ SUCCÈS : {len(df)} produits sauvegardés dans {output_path}")
            return df
        else:
            logger.warning("❌ Aucun produit trouvé.")
            return pd.DataFrame()

def main():
    # ⚠️ headless=False pour vérifier le bon fonctionnement
    scraper = JumiaScraper(headless=False, slow_mo=100)
    
    # Liste des mots-clés (cohérente avec Amazon)
    keywords = ["smartphone", "iphone", "samsung galaxy", "android phone", "xiaomi"]
    
    all_dfs = [] 

    for keyword in keywords:
        print(f"\n🚀 Lancement du scraping Jumia pour : {keyword}")
        # On limite à 5 pages par mot-clé 
        df = scraper.scrape(keyword, max_pages=5)
        
        if not df.empty:
            print(f"✅ {len(df)} produits récupérés pour '{keyword}'")
            all_dfs.append(df)
        else:
            print(f"⚠️ Aucun produit pour '{keyword}'")
    
    # Fusionner tous les résultats
    if all_dfs:
        final_df = pd.concat(all_dfs, ignore_index=True)
        
        # Sauvegarde finale
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = DATA_DIR / f"jumia_global_{timestamp}.csv"
        final_df.to_csv(output_path, index=False, encoding='utf-8')
        
        print(f"\n✅ TERMINÉ ! Total de produits récupérés : {len(final_df)}")
        print(f"📁 Fichier sauvegardé : {output_path}")
    else:
        print("❌ Aucun produit récupéré.")

if __name__ == "__main__":
    main()