"""
Application principale Streamlit - Analyse E-commerce
Auteur: [Votre Nom]
Date: [Date]
Description: Dashboard interactif pour l'analyse des produits e-commerce
"""

import streamlit as st
import os
from pathlib import Path

# Configuration de la page
st.set_page_config(
    page_title="Analyse E-commerce - Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titre principal
st.title("📊 Dashboard d'Analyse E-commerce")
st.markdown("""
**Analyse concurrentielle entre marques** - Samsung, Apple, Xiaomi, etc.
            
*Données extraites d'Amazon et Jumia - Projet académique d'excellence*
""")

# Sidebar avec navigation
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3144/3144456.png", width=100)
    st.title("Navigation")
    
    st.markdown("---")
    st.subheader("📈 Pages d'Analyse")
    
    # Options de navigation
    page_options = {
        "📊 Dashboard Global": "1_dashboard",
        "💰 Analyse Prix vs Marques": "2_prix_marques", 
        "😊 Analyse NLP & Sentiments": "3_sentiment_nlp",
        "🎯 Recommandations Produits": "4_recommandation"
    }
    
    for page_name, page_file in page_options.items():
        if st.button(page_name, use_container_width=True):
            st.switch_page(f"pages/{page_file}.py")
    
    st.markdown("---")
    
    # Informations techniques
    st.subheader("ℹ️ Informations")
    st.info("""
    **Contexte du projet:**
    - Web scraping Amazon & Jumia
    - Analyse NLP avec Transformers
    - Clustering textuel
    - Prédiction de prix
    """)
    
    # Afficher les données chargées
    st.subheader("📁 Données")
    try:
        from utils.load_data import load_processed_data
        df = load_processed_data()
        st.success(f"✅ {len(df)} produits chargés")
        st.caption(f"{df['brand'].nunique()} marques analysées")
    except Exception as e:
        st.error(f"❌ Erreur de chargement: {e}")

# Page d'accueil
st.header("Bienvenue dans l'analyse e-commerce")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="🎯 Objectif Principal", 
        value="Analyse Marques",
        delta="Concurrence entre marques"
    )

with col2:
    st.metric(
        label="📊 Couverture Données", 
        value="2 Plateformes",
        delta="Amazon + Jumia"
    )

with col3:
    st.metric(
        label="🤖 Technologie", 
        value="NLP Avancé",
        delta="Transformers"
    )

# Section d'introduction
st.markdown("---")
st.subheader("🎯 Objectifs de l'Analyse")

objectif_cols = st.columns(2)

with objectif_cols[0]:
    st.markdown("""
    **🔍 Analyse Concurrentielle:**
    - Comparaison des prix entre marques
    - Positionnement marché
    - Stratégies de pricing
    
    **😊 Perception Client:**
    - Analyse de sentiments
    - Corrélation prix/sentiment
    - Satisfaction par marque
    """)

with objectif_cols[1]:
    st.markdown("""
    **📈 Insights Actionnables:**
    - Produits sous/sur-évalués
    - Opportunités marché
    - Recommandations stratégiques
    
    **🎓 Valeur Académique:**
    - Méthodologie rigoureuse
    - Visualisations professionnelles
    - Insights data-driven
    """)

# Instructions
with st.expander("📋 Comment utiliser cette application"):
    st.markdown("""
    1. **Dashboard Global**: Vue d'ensemble avec KPIs et filtres
    2. **Analyse Prix vs Marques**: Comparaison concurrentielle détaillée  
    3. **Analyse NLP & Sentiments**: Perception client et scores de sentiment
    4. **Recommandations**: Produits à fort potentiel selon plusieurs critères
    
    ⚠️ **Important**: L'analyse se concentre sur la concurrence entre **marques**, pas entre plateformes.
    """)

# Footer
st.markdown("---")
st.caption("""
Projet académique d'excellence - Analyse E-commerce | 
Technologies: Streamlit, Pandas, Seaborn, Matplotlib, Plotly, NLP Transformers
""")