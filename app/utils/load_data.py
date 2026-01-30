"""
Module de chargement des données
Gestion centralisée du chargement des données traitées
"""

import pandas as pd
import os
from pathlib import Path
import streamlit as st

@st.cache_data
def load_processed_data():
    """
    Charge le fichier final_products.csv depuis data/processed/
    
    Returns:
        pd.DataFrame: DataFrame contenant les données des produits
    """
    try:
        # Déterminer le chemin du fichier
        base_path = Path(__file__).parent.parent.parent
        data_path = base_path / "data" / "processed" / "products_cleaned.csv"
        
        # Vérifier si le fichier existe
        if not data_path.exists():
            # Essayer un chemin alternatif
            data_path = base_path / "processed" / "products_cleaned.csv"
            if not data_path.exists():
                raise FileNotFoundError(f"Fichier non trouvé: {data_path}")
        
        # Charger les données
        df = pd.read_csv(data_path)
        
        # Nettoyage basique des colonnes
        if 'prix' in df.columns:
            df['prix'] = pd.to_numeric(df['prix'], errors='coerce')
        if 'note' in df.columns:
            df['note'] = pd.to_numeric(df['note'], errors='coerce')
        if 'sentiment_score' in df.columns:
            df['sentiment_score'] = pd.to_numeric(df['sentiment_score'], errors='coerce')
        
        # Nettoyer les marques
        if 'brand' in df.columns:
            df['brand'] = df['brand'].astype(str).str.strip().str.title()
        
        return df
    
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {str(e)}")
        # Retourner un DataFrame vide en cas d'erreur
        return pd.DataFrame()

def get_brand_list(df):
    """Retourne la liste des marques uniques"""
    if not df.empty and 'brand' in df.columns:
        return sorted(df['brand'].dropna().unique().tolist())
    return []

def get_category_list(df):
    """Retourne la liste des catégories uniques"""
    if not df.empty and 'category' in df.columns:
        return sorted(df['category'].dropna().unique().tolist())
    return []

def filter_data(df, brand_filter=None, category_filter=None, sentiment_filter=None):
    """
    Filtre les données selon les critères spécifiés
    
    Args:
        df: DataFrame source
        brand_filter: Liste des marques à inclure
        category_filter: Liste des catégories à inclure
        sentiment_filter: Tuple (min, max) pour le score de sentiment
    
    Returns:
        pd.DataFrame: DataFrame filtré
    """
    filtered_df = df.copy()
    
    # Appliquer les filtres
    if brand_filter and len(brand_filter) > 0:
        filtered_df = filtered_df[filtered_df['brand'].isin(brand_filter)]
    
    if category_filter and len(category_filter) > 0:
        filtered_df = filtered_df[filtered_df['category'].isin(category_filter)]
    
    if sentiment_filter and len(sentiment_filter) == 2:
        min_sent, max_sent = sentiment_filter
        filtered_df = filtered_df[
            (filtered_df['sentiment_score'] >= min_sent) & 
            (filtered_df['sentiment_score'] <= max_sent)
        ]
    
    return filtered_df