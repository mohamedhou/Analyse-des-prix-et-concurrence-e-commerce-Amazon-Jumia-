"""
Analyse des Prix par Marque - Concurrence entre marques
"""

import streamlit as st
import pandas as pd
import numpy as np
from utils.load_data import load_processed_data, filter_data, get_brand_list
from utils.plots import plot_price_boxplot_by_brand, plot_brand_positioning

# Configuration de la page
st.set_page_config(
    page_title="Analyse Prix vs Marques - E-commerce",
    layout="wide"
)

st.title("💰 Analyse Concurrentielle: Prix vs Marques")
st.markdown("""
**Analyse détaillée des stratégies de pricing et positionnement concurrentiel entre marques**
            
*Focus sur la concurrence entre marques (Samsung, Apple, Xiaomi, etc.) - pas entre plateformes*
""")

# Charger les données
@st.cache_data
def load_data():
    return load_processed_data()

df = load_data()

if df.empty:
    st.error("⚠️ Aucune donnée n'a pu être chargée.")
    st.stop()

# Sidebar avec filtres
with st.sidebar:
    st.header("⚙️ Paramètres d'Analyse")
    
    # Sélection des marques à comparer
    all_brands = get_brand_list(df)
    st.subheader("🎯 Sélection des marques")
    
    comparison_mode = st.radio(
        "Mode de comparaison:",
        ["Top 10 marques", "Sélection manuelle", "Toutes les marques"],
        index=0
    )
    
    if comparison_mode == "Top 10 marques":
        selected_brands = all_brands[:10] if len(all_brands) > 10 else all_brands
    elif comparison_mode == "Sélection manuelle":
        selected_brands = st.multiselect(
            "Choisissez les marques à comparer:",
            options=all_brands,
            default=all_brands[:5] if len(all_brands) > 5 else all_brands
        )
    else:
        selected_brands = all_brands
    
    st.markdown("---")
    
    # Options d'affichage
    st.subheader("📊 Options de visualisation")
    show_outliers = st.checkbox("Afficher les outliers", value=True)
    color_palette = st.selectbox(
        "Palette de couleurs:",
        ["viridis", "plasma", "coolwarm", "Set2", "husl"],
        index=0
    )
    
    # Filtre de prix
    st.subheader("💵 Filtre de prix")
    max_price = df['prix'].max()
    price_range = st.slider(
        "Plage de prix (€):",
        0.0, float(max_price * 1.1), 
        (0.0, float(max_price)),
        step=10.0
    )
    
    st.markdown("---")
    st.info(f"**Analyse en cours:** {len(selected_brands)} marques sélectionnées")

# Filtrer les données
filtered_df = df[
    df['brand'].isin(selected_brands) & 
    (df['prix'] >= price_range[0]) & 
    (df['prix'] <= price_range[1])
]

if filtered_df.empty:
    st.warning("⚠️ Aucune donnée ne correspond aux filtres sélectionnés.")
    st.stop()

# Section 1: Vue d'ensemble comparative
st.header("📊 Vue d'Ensemble Comparative")

# KPIs comparatifs
st.subheader("Indicateurs clés par marque")

# Calcul des statistiques par marque
brand_stats = filtered_df.groupby('brand').agg({
    'prix': ['mean', 'median', 'std', 'count'],
    'sentiment_score': 'mean' if 'sentiment_score' in filtered_df.columns else lambda x: None,
    'note': 'mean' if 'note' in filtered_df.columns else lambda x: None
}).round(2)

# Aplatir les colonnes
brand_stats.columns = ['_'.join(col).strip() for col in brand_stats.columns.values]
brand_stats = brand_stats.rename(columns={
    'prix_mean': '💰 Prix Moyen',
    'prix_median': '📊 Prix Médian',
    'prix_std': '📈 Écart-type',
    'prix_count': '📦 Nombre Produits'
})

if 'sentiment_score' in filtered_df.columns:
    brand_stats = brand_stats.rename(columns={'sentiment_score_mean': '😊 Sentiment Moyen'})
if 'note' in filtered_df.columns:
    brand_stats = brand_stats.rename(columns={'note_mean': '⭐ Note Moyenne'})

# Afficher le tableau
st.dataframe(
    brand_stats.sort_values('💰 Prix Moyen', ascending=False),
    use_container_width=True,
    height=400
)

st.markdown("---")

# Section 2: Visualisations
st.header("📈 Visualisations Détaillées")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Distribution des prix par marque")
    
    # Boxplot interactif
    fig_box = plot_price_boxplot_by_brand(filtered_df, top_n=len(selected_brands))
    st.pyplot(fig_box)
    
    with st.expander("🔍 Interprétation du boxplot"):
        st.markdown("""
        **Lecture du graphique:**
        - **Boîte (IQR):** 50% des produits sont dans cette plage de prix
        - **Ligne médiane:** Prix médian de la marque
        - **Moustaches:** Plage normale des prix (1.5 × IQR)
        - **Points:** Outliers (produits exceptionnellement chers ou bon marché)
        
        **Insights:**
        - Large boîte → Grande variété de prix dans la marque
        - Position haute → Positionnement premium
        - Nombreux outliers → Stratégie de gamme large
        """)

with col2:
    st.subheader("2. Positionnement marché des marques")
    
    # Bubble chart positionnement
    fig_pos = plot_brand_positioning(filtered_df)
    st.plotly_chart(fig_pos, use_container_width=True)
    
    with st.expander("🎯 Stratégies de positionnement"):
        st.markdown("""
        **Quadrants de positionnement:**
        
        1. **🔴 Premium:** Prix élevé, sentiment faible → Risque de surévaluation
        2. **🟢 Excellence:** Prix élevé, sentiment élevé → Positionnement justifié
        3. **🟡 Économique:** Prix bas, sentiment faible → Marché entrée de gamme
        4. **🔵 Meilleur rapport Q/P:** Prix bas, sentiment élevé → Opportunités
        
        **Recommandations:**
        - Cibler les marques du quadrant 4 pour l'achat
        - Analyser les marques du quadrant 1 pour la concurrence
        """)

st.markdown("---")

# Section 3: Analyse détaillée par marque
st.header("🔬 Analyse Granulaire par Marque")

# Sélection d'une marque pour analyse détaillée
selected_brand = st.selectbox(
    "Sélectionnez une marque pour analyse détaillée:",
    options=sorted(selected_brands),
    index=0 if selected_brands else None
)

if selected_brand:
    brand_data = filtered_df[filtered_df['brand'] == selected_brand]
    
    if not brand_data.empty:
        # Métriques de la marque
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            prix_moyen = brand_data['prix'].mean()
            st.metric("Prix moyen", f"{prix_moyen:.2f}€")
        
        with col2:
            if 'sentiment_score' in brand_data.columns:
                sentiment_moyen = brand_data['sentiment_score'].mean()
                st.metric("Sentiment moyen", f"{sentiment_moyen:.2f}/5")
            else:
                st.metric("Sentiment moyen", "N/A")
        
        with col3:
            if 'note' in brand_data.columns:
                note_moyenne = brand_data['note'].mean()
                st.metric("Note moyenne", f"{note_moyenne:.2f}/5")
            else:
                st.metric("Note moyenne", "N/A")
        
        with col4:
            nb_produits = len(brand_data)
            st.metric("Nombre produits", nb_produits)
        
        # Top produits de la marque
        st.subheader(f"Top 5 produits {selected_brand} par note")
        
        sort_column = 'note' if 'note' in brand_data.columns else 'prix'
        top_produits = brand_data.nlargest(5, sort_column)[['titre', 'prix']]
        
        if 'sentiment_score' in brand_data.columns:
            top_produits['sentiment_score'] = brand_data['sentiment_score']
        if 'note' in brand_data.columns:
            top_produits['note'] = brand_data['note']
        if 'category' in brand_data.columns:
            top_produits['category'] = brand_data['category']
        
        top_produits = top_produits.rename(columns={
            'titre': 'Produit',
            'prix': 'Prix (€)',
            'sentiment_score': 'Sentiment',
            'note': 'Note',
            'category': 'Catégorie'
        })
        
        st.dataframe(top_produits, use_container_width=True, hide_index=True)
        
        # Distribution des prix de la marque
        st.subheader("Distribution des prix")
        
        # Histogramme des prix
        hist_values = np.histogram(brand_data['prix'].dropna(), bins=20)
        chart_data = pd.DataFrame({
            'Plage de prix': [f"{hist_values[1][i]:.0f}-{hist_values[1][i+1]:.0f}€" 
                             for i in range(len(hist_values[0]))],
            'Nombre de produits': hist_values[0]
        })
        
        st.bar_chart(chart_data.set_index('Plage de prix'))

st.markdown("---")

# Section 4: Insights stratégiques
st.header("🎯 Insights Stratégiques et Recommandations")

# Calcul des insights
insight_cols = st.columns(2)

with insight_cols[0]:
    st.subheader("🏆 Marques Performantes")
    
    # Marques avec meilleur rapport qualité-prix
    if 'sentiment_score' in filtered_df.columns:
        brand_stats = filtered_df.groupby('brand').agg({
            'prix': 'mean',
            'sentiment_score': 'mean'
        })
        brand_stats['rapport_qp'] = brand_stats['sentiment_score'] / brand_stats['prix']
        
        # Top 3 meilleur rapport Q/P
        top_rapport = brand_stats.nlargest(3, 'rapport_qp')
        
        for idx, (marque, stats) in enumerate(top_rapport.iterrows()):
            st.success(f"**{idx+1}. {marque}**\n"
                      f"Rapport Q/P: {stats['rapport_qp']:.4f} | "
                      f"Prix: {stats['prix']:.2f}€ | "
                      f"Sentiment: {stats['sentiment_score']:.2f}")
    else:
        st.info("Analyse du rapport qualité-prix non disponible (sentiment non calculé)")

with insight_cols[1]:
    st.subheader("⚠️ Marques à Surveiller")
    
    if 'sentiment_score' in filtered_df.columns:
        # Marques surévaluées (prix élevé, sentiment bas)
        brand_stats = filtered_df.groupby('brand').agg({
            'prix': 'mean',
            'sentiment_score': 'mean'
        })
        
        prix_median = brand_stats['prix'].median()
        sentiment_median = brand_stats['sentiment_score'].median()
        
        surevaluees = brand_stats[
            (brand_stats['prix'] > prix_median) & 
            (brand_stats['sentiment_score'] < sentiment_median)
        ]
        
        if not surevaluees.empty:
            for idx, (marque, stats) in enumerate(surevaluees.head(3).iterrows()):
                st.warning(f"**{marque}** - Possible surévaluation\n"
                          f"Prix: {stats['prix']:.2f}€ (↑{((stats['prix']-prix_median)/prix_median*100):.1f}%) | "
                          f"Sentiment: {stats['sentiment_score']:.2f} (↓{((sentiment_median-stats['sentiment_score'])/sentiment_median*100):.1f}%)")
        else:
            st.info("Aucune marque clairement surévaluée détectée.")
    else:
        st.info("Analyse des marques surévaluées non disponible (sentiment non calculé)")

# Recommandations générales
st.subheader("💡 Recommandations Commerciales")

recommendations = [
    "**Pricing stratégique:** Analyser les écarts de prix entre marques similaires",
    "**Positionnement:** Identifier les niches non couvertes par les marques premium",
]

if selected_brand and not brand_data.empty:
    recommendations.append(f"**Opportunité:** Cibler les produits {selected_brand} pour leur bon rapport qualité-prix")

recommendations.extend([
    "**Veille concurrentielle:** Surveiller les marques en croissance dans le quadrant 'Meilleur rapport Q/P'",
    "**Marketing:** Mettre en avant le rapport qualité-prix pour les marques performantes"
])

for rec in recommendations:
    st.markdown(f"- {rec}")

# Footer
st.markdown("---")
st.caption("""
Analyse Prix vs Marques - Projet E-commerce | 
Focus exclusif sur la concurrence entre marques (Amazon et Jumia combinés)
""")