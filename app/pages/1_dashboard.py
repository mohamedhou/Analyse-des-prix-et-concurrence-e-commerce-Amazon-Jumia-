"""
Dashboard Global - Vue d'ensemble des données
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from utils.load_data import load_processed_data, filter_data, get_brand_list, get_category_list
from utils.plots import create_kpi_metrics, plot_price_vs_features

# Charger le CSS
def load_css():
    css_path = Path(__file__).parent.parent / "styles.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Global - Analyse E-commerce",
    layout="wide"
)

st.title("📊 Dashboard Global")
st.markdown("Vue d'ensemble des produits e-commerce avec filtres interactifs")

# Charger les données
@st.cache_data
def load_data():
    return load_processed_data()

df = load_data()

if df.empty:
    st.error("⚠️ Aucune donnée n'a pu être chargée. Vérifiez le fichier final_products.csv")
    st.stop()

# Sidebar avec filtres
with st.sidebar:
    st.header("🔍 Filtres d'Analyse")
    
    # Filtre par marque
    all_brands = get_brand_list(df)
    selected_brands = st.multiselect(
        "Sélectionnez les marques:",
        options=all_brands,
        default=all_brands[:5] if len(all_brands) > 5 else all_brands,
        help="Choisissez une ou plusieurs marques à analyser"
    )
    
    # Filtre par catégorie
    all_categories = get_category_list(df)
    selected_categories = st.multiselect(
        "Sélectionnez les catégories:",
        options=all_categories,
        default=all_categories[:3] if len(all_categories) > 3 else all_categories,
        help="Choisissez une ou plusieurs catégories"
    )
    
    # Filtre par score de sentiment
    st.subheader("📊 Score de Sentiment")
    sentiment_range = st.slider(
        "Plage de scores de sentiment:",
        min_value=1.0,
        max_value=5.0,
        value=(3.0, 5.0),
        step=0.1,
        help="Filtrer par score de sentiment minimum et maximum"
    )
    
    # Bouton de réinitialisation
    if st.button("🔄 Réinitialiser les filtres", width='stretch'):
        selected_brands = all_brands
        selected_categories = all_categories
        sentiment_range = (1.0, 5.0)
    
    st.markdown("---")
    st.info(f"**Base de données:** {len(df)} produits au total")

# Appliquer les filtres
filtered_df = filter_data(
    df, 
    brand_filter=selected_brands,
    category_filter=selected_categories,
    sentiment_filter=sentiment_range
)

# Afficher les statistiques de filtrage
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Produits filtrés", len(filtered_df), 
              f"{len(filtered_df)/len(df)*100:.1f}% du total")
with col2:
    st.metric("Marques sélectionnées", len(selected_brands))
with col3:
    st.metric("Score de sentiment moyen", f"{filtered_df['sentiment_score'].mean():.2f}")

st.markdown("---")

# Section 1: KPIs Principaux
st.header("📈 Indicateurs Clés de Performance (KPIs)")

# Calculer les métriques
metrics = create_kpi_metrics(filtered_df)

# Afficher les KPIs dans des colonnes
kpi_cols = st.columns(4)

with kpi_cols[0]:
    st.metric(
        label="Nombre total de produits",
        value=f"{metrics.get('total_produits', 0):,}",
        delta=f"{metrics.get('marques_uniques', 0)} marques"
    )

with kpi_cols[1]:
    st.metric(
        label="Prix moyen",
        value=f"{metrics.get('prix_moyen', 0):.2f}€",
        delta=f"Médiane: {metrics.get('prix_median', 0):.2f}€"
    )

with kpi_cols[2]:
    st.metric(
        label="Note moyenne",
        value=f"{metrics.get('note_moyenne', 0):.2f}/5",
        delta="Satisfaction client"
    )

with kpi_cols[3]:
    st.metric(
        label="Sentiment moyen",
        value=f"{metrics.get('sentiment_moyen', 0):.2f}/5",
        delta="Perception NLP"
    )

# Meilleures marques par sentiment
st.subheader("🏆 Top 3 des marques par sentiment client")
if 'top_marques_sentiment' in metrics and metrics['top_marques_sentiment']:
    top_cols = st.columns(3)
    for idx, marque in enumerate(metrics['top_marques_sentiment']):
        marque_sentiment = filtered_df[filtered_df['brand'] == marque]['sentiment_score'].mean()
        with top_cols[idx]:
            st.info(f"**{marque}**\n\nScore: {marque_sentiment:.2f}/5")

st.markdown("---")

# Section 2: Distribution des données
st.header("📊 Distribution des Données")

tab1, tab2, tab3 = st.tabs(["Vue d'ensemble", "Par marque", "Par catégorie"])

with tab1:
    # Statistiques descriptives
    st.subheader("Statistiques descriptives des prix")
    if 'prix' in filtered_df.columns:
        desc_stats = filtered_df['prix'].describe()
        st.dataframe(desc_stats, width='stretch')
    
    # Histogramme des prix
    st.subheader("Distribution des prix")
    fig = plot_price_vs_features(filtered_df)
    st.pyplot(fig)

with tab2:
    # Prix moyen par marque
    st.subheader("Prix moyen par marque")
    if not filtered_df.empty and 'brand' in filtered_df.columns:
        prix_par_marque = filtered_df.groupby('brand').agg({
            'prix': ['mean', 'count', 'std'],
            'sentiment_score': 'mean',
            'note': 'mean'
        }).round(2)
        
        # Renommer les colonnes
        prix_par_marque.columns = ['_'.join(col).strip() for col in prix_par_marque.columns.values]
        prix_par_marque = prix_par_marque.rename(columns={
            'prix_mean': 'Prix Moyen',
            'prix_count': 'Nombre Produits',
            'prix_std': 'Écart-type Prix',
            'sentiment_score_mean': 'Sentiment Moyen',
            'note_mean': 'Note Moyenne'
        })
        
        st.dataframe(prix_par_marque.sort_values('Prix Moyen', ascending=False), 
                    width='stretch')

with tab3:
    # Analyse par catégorie
    st.subheader("Analyse par catégorie")
    if not filtered_df.empty and 'category' in filtered_df.columns:
        cat_stats = filtered_df.groupby('category').agg({
            'prix': ['mean', 'count', 'min', 'max'],
            'sentiment_score': 'mean'
        }).round(2)
        
        cat_stats.columns = ['_'.join(col).strip() for col in cat_stats.columns.values]
        cat_stats = cat_stats.rename(columns={
            'prix_mean': 'Prix Moyen',
            'prix_count': 'Nombre Produits',
            'prix_min': 'Prix Min',
            'prix_max': 'Prix Max',
            'sentiment_score_mean': 'Sentiment Moyen'
        })
        
        st.dataframe(cat_stats.sort_values('Nombre Produits', ascending=False), 
                    width='stretch')

st.markdown("---")

# Section 3: Données brutes avec filtres
st.header("🔍 Exploration des Données")

with st.expander("📋 Aperçu des données filtrées", expanded=False):
    # Sélection des colonnes à afficher
    available_columns = filtered_df.columns.tolist()
    default_columns = ['titre', 'brand', 'category', 'prix', 'note', 'sentiment_score']
    selected_columns = st.multiselect(
        "Colonnes à afficher:",
        options=available_columns,
        default=default_columns
    )
    
    if selected_columns:
        # Trier les données
        sort_by = st.selectbox("Trier par:", options=selected_columns, index=3)
        sort_order = st.radio("Ordre:", ["Croissant", "Décroissant"], horizontal=True)
        
        ascending = sort_order == "Croissant"
        display_df = filtered_df[selected_columns].sort_values(sort_by, ascending=ascending)
        
        st.dataframe(
            display_df,
            width='stretch',
            hide_index=True
        )
        
        # Option de téléchargement
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger les données filtrées (CSV)",
            data=csv,
            file_name="donnees_filtrees.csv",
            mime="text/csv",
            width='stretch'
        )

# Section 4: Insights automatiques
st.header("💡 Insights Automatiques")

insight_cols = st.columns(2)

with insight_cols[0]:
    st.subheader("📈 Tendances détectées")
    
    # Calculer quelques insights
    if not filtered_df.empty:
        # Marque la plus chère
        plus_cher = filtered_df.loc[filtered_df['prix'].idxmax()]
        st.info(f"**Produit le plus cher:** {plus_cher['titre'][:50]}...\n"
                f"Prix: {plus_cher['prix']:.2f}€ | Marque: {plus_cher['brand']}")
        
        # Meilleur rapport qualité-prix
        if 'sentiment_score' in filtered_df.columns:
            filtered_df['rapport_qp'] = filtered_df['sentiment_score'] / filtered_df['prix']
            meilleur_rapport = filtered_df.loc[filtered_df['rapport_qp'].idxmax()]
            st.success(f"**Meilleur rapport qualité-prix:** {meilleur_rapport['titre'][:50]}...\n"
                      f"Sentiment: {meilleur_rapport['sentiment_score']:.2f} | Prix: {meilleur_rapport['prix']:.2f}€")

with insight_cols[1]:
    st.subheader("🎯 Recommandations")
    
    recommendations = []
    
    # Identifier les opportunités
    prix_moyen = filtered_df['prix'].mean()
    sentiment_moyen = filtered_df['sentiment_score'].mean()
    
    # Produits sous-évalués
    sous_evalues = filtered_df[
        (filtered_df['prix'] < prix_moyen) & 
        (filtered_df['sentiment_score'] > sentiment_moyen)
    ]
    
    if len(sous_evalues) > 0:
        recommendations.append(f"**{len(sous_evalues)} produits sous-évalués** détectés")
    
    # Marques performantes
    if 'brand' in filtered_df.columns:
        marque_perf = filtered_df.groupby('brand').agg({
            'sentiment_score': 'mean',
            'prix': 'mean'
        })
        marque_perf['rapport'] = marque_perf['sentiment_score'] / marque_perf['prix']
        
        if not marque_perf.empty:
            top_marque = marque_perf['rapport'].idxmax()
            st.info(f"**Meilleure marque valeur:** {top_marque}")
    
    for rec in recommendations:
        st.success(rec)

# Footer
st.markdown("---")
st.caption("Dashboard Global - Analyse E-commerce | Données mises à jour automatiquement")