import pandas as pd
import numpy as np
from pathlib import Path
import glob
import os
import sys

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

    def get_latest_file(self, keyword):
        """Trouve le fichier le plus récent contenant le mot-clé dans data/raw"""
        # On cherche tous les fichiers csv contenant le mot clé (amazon ou jumia)
        search_pattern = str(RAW_DIR / f"*{keyword}*.csv")
        files = glob.glob(search_pattern)
        
        if not files:
            print(f"⚠️ Aucun fichier trouvé pour '{keyword}' dans {RAW_DIR}")
            return None
        
        # On trie par date de modification pour prendre le dernier
        latest_file = max(files, key=os.path.getctime)
        print(f"📄 Fichier trouvé ({keyword}) : {Path(latest_file).name}")
        return latest_file

    def clean_text(self, text):
        """Nettoyage basique du texte pour le NLP"""
        if pd.isna(text):
            return ""
        text = str(text).lower()
        text = text.replace('\n', ' ').strip()
        return text

    def standardize_amazon(self, df):
        """Transforme le CSV Amazon au format standard"""
        df = df.copy()
        
        # Sélection et renommage des colonnes
        # On veut : [titre, prix, note, nb_avis, lien, source, id]
        
        # Gestion des colonnes manquantes (au cas où)
        if 'asin' not in df.columns: df['asin'] = np.nan
        if 'nb_avis' not in df.columns: df['nb_avis'] = 0
        
        df = df.rename(columns={
            'asin': 'id_produit',
            'date_scraping': 'date'
        })
        
        # S'assurer que les prix sont des floats
        df['prix'] = pd.to_numeric(df['prix'], errors='coerce')
        
        # Colonnes finales
        cols = ['id_produit', 'titre', 'prix', 'note', 'nb_avis', 'lien', 'source', 'date']
        # On ne garde que les colonnes qui existent
        cols = [c for c in cols if c in df.columns]
        
        return df[cols]

    def standardize_jumia(self, df):
        """Transforme le CSV Jumia au format standard"""
        df = df.copy()
        
        # Jumia n'a pas toujours nb_avis, on crée la colonne si besoin
        if 'nb_avis' not in df.columns:
            df['nb_avis'] = 0
            
        # Renommage
        df = df.rename(columns={
            'date_scraping': 'date'
        })
        
        # S'assurer que les prix sont des floats
        df['prix'] = pd.to_numeric(df['prix'], errors='coerce')
        
        # Colonnes finales
        cols = ['id_produit', 'titre', 'prix', 'note', 'nb_avis', 'lien', 'source', 'date']
        cols = [c for c in cols if c in df.columns]
        
        return df[cols]

    def run(self):
        # 1. Chargement des fichiers
        file_amazon = self.get_latest_file("amazon")
        file_jumia = self.get_latest_file("jumia")
        
        if not file_amazon or not file_jumia:
            print("❌ Impossible de fusionner : il manque un des fichiers sources.")
            return

        df_amazon = pd.read_csv(file_amazon)
        df_jumia = pd.read_csv(file_jumia)

        print(f"📊 Lignes brutes -> Amazon: {len(df_amazon)}, Jumia: {len(df_jumia)}")

        # 2. Standardisation
        df_amazon_clean = self.standardize_amazon(df_amazon)
        df_jumia_clean = self.standardize_jumia(df_jumia)

        # 3. Fusion
        df_final = pd.concat([df_amazon_clean, df_jumia_clean], ignore_index=True)

        # 4. Nettoyage global
        # Supprimer les lignes sans prix (inutile pour l'analyse)
        initial_len = len(df_final)
        df_final = df_final.dropna(subset=['prix'])
        print(f"🗑️ {initial_len - len(df_final)} produits sans prix supprimés.")

        # Remplir les NaN des notes par la moyenne (ou 0, au choix)
        # Pour ce projet, on met -1 pour dire "pas de note"
        df_final['note'] = df_final['note'].fillna(-1)
        df_final['nb_avis'] = df_final['nb_avis'].fillna(0)

        # Nettoyage NLP du titre (création d'une colonne clean_title)
        df_final['titre_clean'] = df_final['titre'].apply(self.clean_text)

        # 5. Sauvegarde
        output_file = PROCESSED_DIR / "products_cleaned.csv"
        df_final.to_csv(output_file, index=False, encoding='utf-8')
        
        print("\n" + "="*50)
        print(f"✅ SUCCÈS ! Dataset fusionné sauvegardé :")
        print(f"📁 {output_file}")
        print(f"📊 Total produits : {len(df_final)}")
        print(f"   - Amazon : {len(df_final[df_final['source'] == 'Amazon'])}")
        print(f"   - Jumia  : {len(df_final[df_final['source'] == 'Jumia'])}")
        print("="*50)

if __name__ == "__main__":
    cleaner = DataCleaner()
    cleaner.run()