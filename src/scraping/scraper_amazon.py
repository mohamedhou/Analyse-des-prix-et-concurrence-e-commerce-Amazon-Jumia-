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
# --- CONFIGURATION AUTOMATIQUE DES CHEMINS (VERSION BLINDÉE) ---
import os

# 1. On cherche d'abord où on est
current_path = Path(__file__).resolve()
project_root = current_path.parent

# 2. On remonte les dossiers jusqu'à trouver 'requirements.txt' (la racine du projet)
# C'est la méthode la plus fiable pour ne jamais se tromper de dossier
found_root = False
for _ in range(5): # On cherche sur 5 niveaux max
    if (project_root / "requirements.txt").exists():
        found_root = True
        break
    project_root = project_root.parent

# 3. Si on ne trouve pas (cas bizarre), on prend le dossier où tu as lancé la commande
if not found_root:
    print("⚠️ Racine du projet non détectée via le fichier, utilisation du dossier courant.")
    PROJECT_ROOT = Path.cwd()
else:
    PROJECT_ROOT = project_root

# 4. Définition des dossiers de sortie
DATA_DIR = PROJECT_ROOT / "data" / "raw"
LOGS_DIR = PROJECT_ROOT / "logs"

# Création physique des dossiers s'ils n'existent pas
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

print(f"📂 Dossier du projet détecté : {PROJECT_ROOT}")
print(f"📂 Dossier de sauvegarde des données : {DATA_DIR}")

# --- CONFIGURATION LOGGING AVANCÉE ---
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
    """
    Scraper Amazon professionnel avec fonctionnalités avancées :
    - Anti-détection robuste
    - Extraction enrichie (vendeur, disponibilité, livraison)
    - Gestion d'erreurs complète
    - Logging détaillé
    - Support multi-devises
    """
    
    def __init__(self, headless: bool = False, slow_mo: int = 100):
        """
        Args:
            headless: Mode sans interface graphique
            slow_mo: Ralentissement en ms pour paraître plus humain
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.stats = {
            'total_products': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'pages_scraped': 0
        }
    
    def _get_random_delays(self) -> tuple:
        """Génère des délais aléatoires pour simuler un comportement humain"""
        scroll_delay = random.uniform(1.5, 3.0)
        page_delay = random.uniform(2.5, 5.0)
        action_delay = random.uniform(0.5, 1.5)
        return scroll_delay, page_delay, action_delay
    
    def _clean_price(self, price_text: str) -> Optional[float]:
        """
        Nettoie et convertit le prix en float
        Gère : '19,99 €', '1 234,56 €', etc.
        """
        if not price_text:
            return None
        try:
            # Enlever le symbole € et espaces
            clean = price_text.replace('€', '').replace(' ', '').strip()
            # Remplacer virgule par point et enlever espaces insécables
            clean = clean.replace(',', '.').replace('\xa0', '')
            return float(clean)
        except ValueError:
            logger.warning(f"Prix impossible à convertir : {price_text}")
            return None
    
    def _extract_rating(self, rating_text: str) -> Optional[float]:
        """
        Extrait la note numérique depuis '4,5 sur 5 étoiles'
        """
        if not rating_text:
            return None
        try:
            # Prendre le premier nombre avant 'sur'
            parts = rating_text.split('sur')[0].strip()
            parts = parts.replace(',', '.')
            return float(parts)
        except (ValueError, IndexError):
            logger.warning(f"Note impossible à extraire : {rating_text}")
            return None
    
    def _extract_reviews_count(self, reviews_text: str) -> Optional[int]:
        """
        Extrait le nombre d'avis depuis '1 234' ou '(1 234)'
        """
        if not reviews_text:
            return None
        try:
            # Enlever parenthèses et espaces
            clean = reviews_text.replace('(', '').replace(')', '').replace(' ', '').replace('\xa0', '')
            return int(clean)
        except ValueError:
            logger.warning(f"Nombre d'avis impossible à extraire : {reviews_text}")
            return None
    
    def _extract_product_data(self, card, asin: str) -> Optional[Dict]:
        """
        Extraction complète et robuste des données d'un produit
        """
        try:
            product_data = {
                'asin': asin,
                'date_scraping': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'Amazon'
            }
            
            # 1. TITRE (Multi-stratégie)
            title = None
            title_selectors = [
                "h2 a span",
                "h2 span",
                "a.a-link-normal span.a-text-normal",
                "a.a-link-normal"
            ]
            for selector in title_selectors:
                if card.locator(selector).count() > 0:
                    title = card.locator(selector).first.inner_text().strip()
                    if title and len(title) > 5:  # Validation minimale
                        break
            
            if not title:
                logger.debug(f"ASIN {asin}: Titre introuvable")
                return None
            product_data['titre'] = title
            
            # 2. PRIX (Avec nettoyage)
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
            reviews_selectors = [
                "span.a-size-base.s-underline-text",
                "span[aria-label*='étoiles']",
                "a span.a-size-base"
            ]
            for selector in reviews_selectors:
                if card.locator(selector).count() > 0:
                    text = card.locator(selector).first.inner_text()
                    if text and any(char.isdigit() for char in text):
                        reviews_raw = text
                        break
            product_data['nb_avis_brut'] = reviews_raw
            product_data['nb_avis'] = self._extract_reviews_count(reviews_raw) if reviews_raw else None
            
            # 5. VENDEUR (Important pour analyse concurrence)
            seller = None
            if card.locator("span.a-size-base-plus.a-color-base").count() > 0:
                seller = card.locator("span.a-size-base-plus.a-color-base").first.inner_text()
            elif card.locator("h5 span").count() > 0:
                seller_text = card.locator("h5 span").first.inner_text()
                if "Visiter" in seller_text:
                    seller = seller_text.replace("Visiter la boutique ", "").strip()
            product_data['vendeur'] = seller
            
            # 6. BADGE PRIME / LIVRAISON
            is_prime = card.locator("i.a-icon-prime").count() > 0
            product_data['prime'] = is_prime
            
            # 7. DISPONIBILITÉ
            availability = "En stock"  # Par défaut
            if card.locator("span.a-color-price").count() > 0:
                avail_text = card.locator("span.a-color-price").first.inner_text()
                if "rupture" in avail_text.lower() or "indisponible" in avail_text.lower():
                    availability = "Rupture de stock"
            product_data['disponibilite'] = availability
            
            # 8. LIEN PRODUIT
            product_data['lien'] = f"https://www.amazon.fr/dp/{asin}"
            
            # 9. IMAGE (Pour analyse visuelle future)
            image_url = None
            if card.locator("img.s-image").count() > 0:
                image_url = card.locator("img.s-image").first.get_attribute("src")
            product_data['image_url'] = image_url
            
            # Validation finale : au minimum titre + (prix OU note)
            if title and (product_data['prix'] is not None or product_data['note'] is not None):
                self.stats['successful_extractions'] += 1
                return product_data
            else:
                logger.debug(f"ASIN {asin}: Données insuffisantes")
                return None
                
        except Exception as e:
            logger.error(f"Erreur extraction ASIN {asin}: {str(e)}")
            self.stats['failed_extractions'] += 1
            return None
    
    def _handle_cookies_banner(self, page):
        """Gestion intelligente des cookies"""
        try:
            # Attendre max 3 secondes pour la bannière
            if page.locator("#sp-cc-accept").is_visible(timeout=3000):
                page.click("#sp-cc-accept")
                logger.info("🍪 Cookies acceptés")
                time.sleep(1)
        except:
            # Pas de bannière ou timeout, on continue
            pass
    
    def _smart_scroll(self, page):
        """
        Scroll intelligent pour charger lazy loading
        Simule un comportement humain
        """
        try:
            scroll_delay, _, _ = self._get_random_delays()
            
            # Scroll par étapes (plus naturel)
            page.evaluate("""
                window.scrollTo({
                    top: document.body.scrollHeight / 2,
                    behavior: 'smooth'
                });
            """)
            time.sleep(scroll_delay)
            
            page.evaluate("""
                window.scrollTo({
                    top: document.body.scrollHeight,
                    behavior: 'smooth'
                });
            """)
            time.sleep(scroll_delay)
            
            # Scroll légèrement vers le haut (comportement réaliste)
            page.evaluate("window.scrollBy(0, -300);")
            time.sleep(0.5)
            
        except Exception as e:
            logger.warning(f"Erreur lors du scroll : {e}")
    
    def scrape(self, keyword: str, max_pages: int = 1, save_json: bool = False) -> pd.DataFrame:
        """
        Fonction principale de scraping
        
        Args:
            keyword: Mot-clé de recherche
            max_pages: Nombre de pages à scraper
            save_json: Sauvegarder aussi en JSON pour backup
            
        Returns:
            DataFrame avec les produits scrapés
        """
        logger.info(f"🚀 Démarrage scraping Amazon : '{keyword}' ({max_pages} pages)")
        products = []
        
        with sync_playwright() as p:
            try:
                # Lancement navigateur avec anti-détection
                browser = p.chromium.launch(
                    headless=self.headless,
                    slow_mo=self.slow_mo,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage'
                    ]
                )
                
                context = browser.new_context(
                    user_agent=random.choice(USER_AGENTS),
                    viewport={'width': 1920, 'height': 1080},
                    locale='fr-FR',
                    timezone_id='Europe/Paris'
                )
                
                # Masquer webdriver
                context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)
                
                page = context.new_page()
                
                # URL avec tri par pertinence
                base_url = f"https://www.amazon.fr/s?k={keyword.replace(' ', '+')}"
                logger.info(f"🌍 Connexion à {base_url}")
                
                page.goto(base_url, timeout=60000, wait_until='domcontentloaded')
                self._handle_cookies_banner(page)
                
                for current_page in range(1, max_pages + 1):
                    logger.info(f"📄 Page {current_page}/{max_pages}")
                    self.stats['pages_scraped'] += 1
                    
                    # Scroll intelligent
                    self._smart_scroll(page)
                    
                    # Attendre le chargement des produits
                    try:
                        page.wait_for_selector('div[data-asin]:not([data-asin=""])', timeout=10000)
                    except PlaywrightTimeout:
                        logger.error("Timeout : Produits non chargés")
                        break
                    
                    # Récupérer tous les produits
                    cards = page.locator('div[data-asin]:not([data-asin=""])').all()
                    logger.info(f"   📦 {len(cards)} produits détectés")
                    
                    for idx, card in enumerate(cards, 1):
                        try:
                            asin = card.get_attribute("data-asin")
                            if not asin or len(asin) != 10:  # ASIN Amazon = 10 caractères
                                continue
                            
                            product = self._extract_product_data(card, asin)
                            if product:
                                products.append(product)
                                if idx % 10 == 0:  # Log tous les 10 produits
                                    logger.info(f"   ✓ {idx}/{len(cards)} produits traités")
                        
                        except Exception as e:
                            logger.error(f"   ⚠️ Erreur produit #{idx}: {str(e)}")
                            continue
                    
                    self.stats['total_products'] = len(products)
                    logger.info(f"   💾 Total accumulé : {len(products)} produits")
                    
                    # PAGINATION
                    if current_page < max_pages:
                        try:
                            _, page_delay, _ = self._get_random_delays()
                            next_btn = page.locator("a.s-pagination-next")
                            
                            if next_btn.is_visible() and next_btn.is_enabled():
                                logger.info(f"➡️  Passage à la page {current_page + 1}...")
                                next_btn.click()
                                time.sleep(page_delay)
                            else:
                                logger.warning("🛑 Bouton 'Suivant' introuvable - Fin de pagination")
                                break
                        
                        except Exception as e:
                            logger.error(f"Erreur pagination : {e}")
                            break
                
                browser.close()
                logger.info("🔒 Navigateur fermé")
            
            except Exception as e:
                logger.error(f"❌ Erreur critique : {str(e)}")
                return pd.DataFrame()
        
        # SAUVEGARDE DES DONNÉES
        return self._save_data(products, keyword, save_json)
    
    def _save_data(self, products: List[Dict], keyword: str, save_json: bool) -> pd.DataFrame:
        """Sauvegarde les données en CSV et optionnellement JSON"""
        if not products:
            logger.warning("❌ Aucun produit récupéré - Aucun fichier créé")
            self._print_stats()
            return pd.DataFrame()
        
        df = pd.DataFrame(products)
        
        # Réorganiser les colonnes pour lisibilité
        column_order = [
            'date_scraping', 'asin', 'titre', 'prix', 'prix_brut',
            'note', 'note_brute', 'nb_avis', 'nb_avis_brut',
            'vendeur', 'prime', 'disponibilite', 'lien', 'image_url', 'source'
        ]
        df = df[[col for col in column_order if col in df.columns]]
        
        # Nom de fichier avec timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_keyword = keyword.replace(' ', '_').replace('/', '_')
        
        # CSV
        csv_filename = f"amazon_{safe_keyword}_{timestamp}.csv"
        csv_path = DATA_DIR / csv_filename
        df.to_csv(csv_path, index=False, encoding='utf-8')
        logger.info(f"✅ CSV sauvegardé : {csv_path}")
        
        # JSON (backup avec métadonnées)
        if save_json:
            json_data = {
                'metadata': {
                    'keyword': keyword,
                    'scraping_date': timestamp,
                    'total_products': len(df),
                    'stats': self.stats
                },
                'products': products
            }
            json_filename = f"amazon_{safe_keyword}_{timestamp}.json"
            json_path = DATA_DIR / json_filename
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ JSON sauvegardé : {json_path}")
        
        self._print_stats()
        return df
    
    def _print_stats(self):
        """Affiche les statistiques du scraping"""
        logger.info("\n" + "="*60)
        logger.info("📊 STATISTIQUES DU SCRAPING")
        logger.info("="*60)
        logger.info(f"Pages scrapées       : {self.stats['pages_scraped']}")
        logger.info(f"Produits trouvés     : {self.stats['total_products']}")
        logger.info(f"Extractions réussies : {self.stats['successful_extractions']}")
        logger.info(f"Extractions échouées : {self.stats['failed_extractions']}")
        if self.stats['total_products'] > 0:
            success_rate = (self.stats['successful_extractions'] / 
                          (self.stats['successful_extractions'] + self.stats['failed_extractions'])) * 100
            logger.info(f"Taux de succès       : {success_rate:.1f}%")
        logger.info("="*60 + "\n")


def main():
    """Fonction principale pour tester le scraper"""
    
    # Configuration
    scraper = AmazonScraper(
        headless=False,  # Mettre True en production
        slow_mo=100      # Ralentissement pour paraître humain
    )
    
    # Exemple 1 : Scraping simple
    print("\n🎯 Test 1 : smartphone (2 pages)")
    df_pcs = scraper.scrape("smartphone", max_pages=2, save_json=True)
    
    if not df_pcs.empty:
        print("\n📋 Aperçu des données :")
        print(df_pcs[['titre', 'prix', 'note', 'nb_avis', 'vendeur']].head(10))
        
        print("\n📈 Statistiques prix :")
        print(df_pcs['prix'].describe())
    
    # Exemple 2 : Autre recherche
    # df_phones = scraper.scrape("iphone 15", max_pages=1)


if __name__ == "__main__":
    main()