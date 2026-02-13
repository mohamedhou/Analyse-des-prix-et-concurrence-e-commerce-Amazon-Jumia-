import pandas as pd
import numpy as np
from pathlib import Path
import glob
import os
import sys
import re

# --- CONFIGURATION DES CHEMINS ---
current_path = Path(__file__).resolve()
project_root = current_path.parent
found_root = False
for _ in range(5):
    if (project_root / "requirements.txt").exists():
        found_root = True
        break
    project_root = project_root.parent
if not found_root: project_root = Path.cwd()

RAW_DIR = project_root / "data" / "raw"
PROCESSED_DIR = project_root / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

class DataCleaner:
    def __init__(self):
        print("🧹 Initialisation du Data Cleaner...")

    def extract_brand(self, text):
        """Extraction des marques avec gestion des alias"""
        if pd.isna(text):
            return 'Unknown'
        
        text_lower = str(text).lower()
        
        # Gestion des alias (iPhone, Galaxy, Redmi, etc.)
        if 'iphone' in text_lower or 'ipad' in text_lower:
            return 'Apple'
        if 'galaxy' in text_lower:
            return 'Samsung'
        if 'redmi' in text_lower or 'pocophone' in text_lower or 'poco' in text_lower:
            return 'Xiaomi'
        if 'pixel' in text_lower:
            return 'Google'
        
        # Liste standard
        brands = [
            'samsung', 'apple', 'huawei', 'xiaomi', 'oppo', 'vivo', 'realme',
            'oneplus', 'google', 'motorola', 'nokia', 'sony', 'lg', 'asus',
            'lenovo', 'tecno', 'infinix', 'wiko', 'honor', 'blackberry'
        ]
        
        for brand in brands:
            if brand in text_lower:
                return brand.capitalize()
        
        return 'Unknown'

    def extract_category(self, text):
        """Classification ULTRA PRÉCISE - VERSION FINALE"""
        if pd.isna(text):
            return 'unknown'

        text_lower = str(text).lower()

        # ===== LISTE NOIRE ULTRA RENFORCÉE =====
        accessory_keywords = [
            # Protection & Coques
            'coque', 'housse', 'étui', 'case', 'cover', 'shell', 'bumper',
            'protection', 'silicone', 'rigid', 'transparent', 'pochette',
            
            # Écran & Film
            'film', 'verre trempé', 'protecteur', 'screen protector', 
            'tempered glass', 'hydrogel', 'pellicule',
            
            # Chargement & Batteries (Capture "Apple Batterie MagSafe")
            'chargeur', 'câble', 'cable', 'adaptateur', 'adapter', 
            'power bank', 'batterie externe', 'batterie', 'wireless charger',
            'charging', 'fast charge', 'plug', 'magsafe', 'powerbank',
            
            # Audio (Capture "DJI Mic")
            'écouteur', 'casque', 'headphone', 'earphone', 'earbud',
            'airpod', 'galaxy buds', 'buds', 'pods', 'speakers', 'enceinte',
            'microphone', 'mic', 'micro', 'cravate', 'sans fil',
            
            # Supports & Stabilisation (Capture "Stabilisateur", "Cardan")
            'trépied', 'tripod', 'gorillapod', 'selfie stick', 'perche',
            'support', 'holder', 'stand', 'mount', 'grip',
            'stabilisateur', 'cardan', 'gimbal', 'steadicam',
            
            # Montres & Bracelets
            'smart watch', 'smartwatch', 'montre connectée', 'watch',
            'bracelet', 'band', 'strap', 'mi band',
            
            # Stockage & Cartes
            'carte mémoire', 'microsd', 'sd card', 'usb', 'clé usb',
            
            # Divers
            'stylet', 's pen', 'apple pencil', 'moniteur', 'kit', 'pack',
            'sim card', 'outil', 'remplacement', 'pièce', 'stick', 'dock'
        ]
        
        # ===== VÉRIFICATION STRICTE =====
        # Si UN SEUL mot d'accessoire est présent -> C'est un accessoire
        if any(acc in text_lower for acc in accessory_keywords):
            return 'accessoire'
        
        # ===== DÉTECTION SMARTPHONE =====
        smartphone_keywords = [
            'smartphone', 'iphone', 'android phone', 'mobile phone',
            'galaxy s', 'galaxy a', 'galaxy z', 'galaxy note',
            'redmi note', 'redmi a', 'poco f', 'poco x',
            'mi 1', 'mi 2', 'mi 3', 'mi 4', 'mi 5', 'mi 6', 'mi 7', 'mi 8', 'mi 9', 'mi 10', 'mi 11', 'mi 12',
            'pixel', 'oneplus', 'oppo find', 'vivo v',
            'huawei p', 'huawei mate',
            'xperia', 'nokia', 'motorola moto'
        ]
        
        if any(kw in text_lower for kw in smartphone_keywords):
            return 'smartphone'
        
        return 'other'

    def _is_real_smartphone_with_bonus(self, text_lower):
        """
        Détecte si c'est un VRAI smartphone avec un bonus accessoire
        Exemple : "Samsung Galaxy S21 + Coque offerte" → True
        Contre-exemple : "Coque de protection iPhone 13" → False
        """
        # Patterns d'accessoires qui commencent le titre
        # Si le titre COMMENCE par un accessoire, ce n'est PAS un smartphone
        accessory_start_patterns = [
            r'^(coque|étui|housse|film|protection|chargeur|câble|support|adaptateur)',
            r'^(casque|écouteur|batterie|kit)',
        ]
        
        for pattern in accessory_start_patterns:
            if re.search(pattern, text_lower):
                return False
        
        # Patterns de vrais smartphones (titre qui commence par une marque/modèle)
        real_smartphone_patterns = [
            r'^(samsung|iphone|xiaomi|google|huawei|oppo|vivo|realme|oneplus)',
            r'^(galaxy|redmi|poco|pixel)',
            r'^smartphone\s+(samsung|apple|xiaomi)',  # "Smartphone Samsung Galaxy..."
        ]
        
        for pattern in real_smartphone_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False

    def extract_brand(self, text):
        if pd.isna(text):
            return 'Unknown'
        
        text_lower = str(text).lower()
        
        # ===== FILTRE ANTI-ACCESSOIRES =====
        # Si c'est déjà classé comme accessoire, on met "Accessory Brand"
        # (à appliquer APRÈS avoir extrait la catégorie)
        
        # --- ALIAS (Crucial) ---
        if 'iphone' in text_lower or 'ipad' in text_lower:
            return 'Apple'
        if 'galaxy' in text_lower and 'watch' not in text_lower:  # ⚠️ Évite "Galaxy Watch"
            return 'Samsung'
        if 'redmi' in text_lower or 'pocophone' in text_lower or 'poco' in text_lower:
            return 'Xiaomi'
        if 'pixel' in text_lower and 'buds' not in text_lower:  # ⚠️ Évite "Pixel Buds"
            return 'Google'
        
        # --- MARQUES STANDARD ---
        brands = [
            'samsung', 'apple', 'huawei', 'xiaomi', 'oppo', 'vivo', 'realme',
            'oneplus', 'google', 'motorola', 'nokia', 'sony', 'lg', 'asus',
            'lenovo', 'tecno', 'infinix', 'wiko', 'honor', 'zte', 'alcatel'
        ]
        
        for brand in brands:
            if brand in text_lower:
                return brand.capitalize()
        
        return 'Unknown'

    def get_latest_file(self, keyword):
        """Trouve le fichier le plus récent (priorité aux fichiers globaux)"""
        search_pattern_global = str(RAW_DIR / f"{keyword}_global_*.csv")
        files_global = glob.glob(search_pattern_global)
        
        if files_global:
            latest_file = max(files_global, key=os.path.getctime)
            print(f"📄 Fichier GLOBAL trouvé ({keyword}) : {Path(latest_file).name}")
            return latest_file

        search_pattern = str(RAW_DIR / f"*{keyword}*.csv")
        files = glob.glob(search_pattern)
        
        if not files:
            print(f"⚠️ Aucun fichier trouvé pour '{keyword}' dans {RAW_DIR}")
            return None
        
        latest_file = max(files, key=os.path.getctime)
        print(f"📄 Fichier trouvé ({keyword}) : {Path(latest_file).name}")
        return latest_file

    def clean_text(self, text):
        if pd.isna(text): return ""
        return str(text).lower().replace('\n', ' ').strip()

    def standardize_amazon(self, df):
        df = df.copy()
        if 'asin' not in df.columns: df['asin'] = np.nan
        if 'nb_avis' not in df.columns: df['nb_avis'] = 0
        
        df = df.rename(columns={'asin': 'id_produit', 'date_scraping': 'date'})
        df['prix'] = pd.to_numeric(df['prix'], errors='coerce')
        
        # Extraction MARQUE et CATÉGORIE
        df['brand'] = df['titre'].apply(self.extract_brand)
        df['category'] = df['titre'].apply(self.extract_category)
        
        cols = ['id_produit', 'titre', 'prix', 'note', 'nb_avis', 'lien', 'source', 'date', 'brand', 'category']
        return df[[c for c in cols if c in df.columns]]

    def standardize_jumia(self, df):
        df = df.copy()
        if 'nb_avis' not in df.columns: df['nb_avis'] = 0
        df = df.rename(columns={'date_scraping': 'date'})
        
        # Normalisation des prix (Jumia -> Euro)
        df['prix'] = pd.to_numeric(df['prix'], errors='coerce')
        df['prix'] = df['prix'] / 11  # Conversion MAD vers Euro
        
        # Extraction MARQUE et CATÉGORIE
        df['brand'] = df['titre'].apply(self.extract_brand)
        df['category'] = df['titre'].apply(self.extract_category)
        
        cols = ['id_produit', 'titre', 'prix', 'note', 'nb_avis', 'lien', 'source', 'date', 'brand', 'category']
        return df[[c for c in cols if c in df.columns]]

    def run(self):
        # 1. Chargement
        file_amazon = self.get_latest_file("amazon")
        file_jumia = self.get_latest_file("jumia")
        
        if not file_amazon or not file_jumia:
            print("❌ Impossible de fusionner : il manque un des fichiers sources.")
            return

        df_amazon = pd.read_csv(file_amazon)
        df_jumia = pd.read_csv(file_jumia)

        print(f"📊 Lignes brutes -> Amazon: {len(df_amazon)}, Jumia: {len(df_jumia)}")

        # 2. Standardisation + Extraction Marques
        df_amazon_clean = self.standardize_amazon(df_amazon)
        df_jumia_clean = self.standardize_jumia(df_jumia)

        # 3. Fusion
        df_final = pd.concat([df_amazon_clean, df_jumia_clean], ignore_index=True)

        # 4. Nettoyage global
                # 4. Nettoyage global
        initial_len = len(df_final)
        df_final = df_final.dropna(subset=['prix'])
        print(f"🗑️ {initial_len - len(df_final)} produits sans prix supprimés.")

        # Afficher la répartition AVANT filtrage
        print(f"\n📊 Répartition par catégorie AVANT filtrage :")
        print(df_final['category'].value_counts())
        
        # Filtrage strict : uniquement smartphones
        df_final = df_final[df_final['category'] == 'smartphone']
        
        # === NOUVEAU FILTRE DE SÉCURITÉ PRIX ===
        # On supprime les produits < 40€ qui sont probablement des accessoires mal classés
        price_threshold = 40.0 
        count_before_price_filter = len(df_final)
        df_final = df_final[df_final['prix'] >= price_threshold]
        print(f"💸 {count_before_price_filter - len(df_final)} produits retirés (prix < {price_threshold}€).")
        # ========================================

        df_final = df_final[df_final['brand'] != 'Unknown'].reset_index(drop=True)

        # Remplir les NaN
        df_final['note'] = df_final['note'].fillna(-1)
        df_final['nb_avis'] = df_final['nb_avis'].fillna(0)

        # 5. Sauvegarde
        output_file = PROCESSED_DIR / "products_cleaned.csv"
        df_final.to_csv(output_file, index=False, encoding='utf-8')
        
        print("\n" + "="*60)
        print(f"✅ SUCCÈS ! Dataset fusionné sauvegardé :")
        print(f"📁 {output_file}")
        print(f"📊 Total produits (SMARTPHONES UNIQUEMENT) : {len(df_final)}")
        print(f"   - Amazon : {len(df_final[df_final['source'] == 'Amazon'])}")
        print(f"   - Jumia  : {len(df_final[df_final['source'] == 'Jumia'])}")
        print(f"🏷️ Marques uniques : {df_final['brand'].nunique()}")
        print(f"📱 Liste des marques : {sorted(df_final['brand'].unique())}")
        print("="*60)

        # Échantillon de validation
        print("\n📋 Échantillon des produits conservés :")
        print(df_final[['titre', 'brand', 'category', 'prix']].head(10))

if __name__ == "__main__":
    cleaner = DataCleaner()
    cleaner.run()