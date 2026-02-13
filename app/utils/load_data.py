import pandas as pd
from pathlib import Path
import sys

# Trouver la racine du projet (remonter de app/utils/ à la racine)
# On suppose que la structure est : racine/app/utils/ce_fichier.py
CURRENT_DIR = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_DIR.parent.parent.parent 
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "products_cleaned.csv"

def load_processed_data():
    """Charge le dataset nettoyé pour l'application"""
    try:
        if not DATA_PATH.exists():
            print(f"❌ Fichier introuvable : {DATA_PATH}")
            return pd.DataFrame()
            
        df = pd.read_csv(DATA_PATH)
        print(f"✅ Données brutes chargées : {len(df)} lignes")
        
        # --- FORCE LE FILTRE SMARTPHONE ---
        if 'category' in df.columns:
            initial_count = len(df)
            df = df[df['category'] == 'smartphone']
            removed_count = initial_count - len(df)
            if removed_count > 0:
                print(f"🧹 Nettoyage App : {removed_count} produits non-smartphones ignorés.")
        
        # --- GESTION DES COLONNES MANQUANTES (FALLBACK NLP) ---
        # Si le NLP n'a pas été lancé, on utilise la note client comme substitut
        if 'sentiment_score' not in df.columns:
            print("⚠️ Colonne 'sentiment_score' absente (NLP non exécuté).")
            if 'note' in df.columns:
                # On utilise la note client comme substitut du sentiment
                df['sentiment_score'] = df['note']
                print("   -> Utilisation de la colonne 'note' comme substitut.")
            else:
                # Si pas de note non plus, on met neutre
                df['sentiment_score'] = 3.0
                print("   -> Valeur neutre (3.0) attribuée par défaut.")
        
        # Idem pour le cluster si nécessaire pour l'affichage
        if 'cluster' not in df.columns:
            df['cluster'] = 0

        print(f"✅ Données finales pour l'App : {len(df)} lignes (Smartphones uniquement)")
        
        # Vérification des colonnes
        required_cols = ['titre', 'prix', 'note', 'brand', 'source']
        for col in required_cols:
            if col not in df.columns:
                print(f"⚠️ Colonne manquante : {col}")
                
        return df
    except Exception as e:
        print(f"❌ Erreur lors du chargement : {e}")
        return pd.DataFrame()
def filter_data(df, brand_filter=None, category_filter=None, sentiment_filter=(1.0, 5.0)):
    """Filtre le dataframe selon les critères de la sidebar"""
    if df.empty:
        return df
        
    # Filtre Marque
    if brand_filter:
        df = df[df['brand'].isin(brand_filter)]
    
    # Filtre Catégorie
    if category_filter:
        df = df[df['category'].isin(category_filter)]
        
    # Filtre Sentiment (si la colonne existe)
    if 'sentiment_score' in df.columns:
        df = df[df['sentiment_score'].between(sentiment_filter[0], sentiment_filter[1])]
        
    return df

def get_brand_list(df):
    """Retourne la liste des marques uniques triées"""
    if 'brand' in df.columns:
        return sorted(df['brand'].unique())
    return []

def get_category_list(df):
    """Retourne la liste des catégories uniques"""
    if 'category' in df.columns:
        return sorted(df['category'].unique())
    return []