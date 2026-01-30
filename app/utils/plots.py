"""
Module de visualisations
Fonctions pour créer des graphiques standardisés
"""

import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from matplotlib import cm

# Configuration des styles
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

def setup_plot_style():
    """Configure le style des graphiques matplotlib"""
    plt.rcParams['figure.figsize'] = (12, 6)
    plt.rcParams['font.size'] = 12
    plt.rcParams['axes.titlesize'] = 16
    plt.rcParams['axes.labelsize'] = 14

def create_kpi_metrics(df):
    """
    Crée une visualisation des KPIs principaux
    
    Args:
        df: DataFrame contenant les données
    
    Returns:
        tuple: (fig, metrics_dict) figure matplotlib et dictionnaire de métriques
    """
    metrics = {}
    
    # Calcul des métriques de base
    metrics['total_produits'] = len(df)
    metrics['marques_uniques'] = df['brand'].nunique()
    
    if 'prix' in df.columns:
        metrics['prix_moyen'] = df['prix'].mean()
        metrics['prix_median'] = df['prix'].median()
    
    if 'note' in df.columns:
        metrics['note_moyenne'] = df['note'].mean()
    
    if 'sentiment_score' in df.columns:
        metrics['sentiment_moyen'] = df['sentiment_score'].mean()
    
    # Meilleures marques par sentiment
    if 'brand' in df.columns and 'sentiment_score' in df.columns:
        brand_sentiment = df.groupby('brand')['sentiment_score'].mean().sort_values(ascending=False)
        metrics['top_marques_sentiment'] = brand_sentiment.head(3).index.tolist()
    
    return metrics

def plot_price_boxplot_by_brand(df, top_n=10):
    """
    Boxplot des prix par marque (top N marques)
    
    Args:
        df: DataFrame
        top_n: Nombre de marques à afficher
    
    Returns:
        matplotlib.figure.Figure: Figure générée
    """
    setup_plot_style()
    
    # Sélectionner les top N marques par nombre de produits
    top_brands = df['brand'].value_counts().head(top_n).index
    df_filtered = df[df['brand'].isin(top_brands)]
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Trier par prix médian
    brand_order = df_filtered.groupby('brand')['prix'].median().sort_values(ascending=False).index
    
    sns.boxplot(
        data=df_filtered,
        x='brand',
        y='prix',
        order=brand_order,
        ax=ax,
        palette='viridis'
    )
    
    ax.set_title(f'Distribution des Prix par Marque (Top {top_n})', fontsize=16, fontweight='bold')
    ax.set_xlabel('Marque', fontsize=14)
    ax.set_ylabel('Prix (€)', fontsize=14)
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3)
    
    # Ajouter une ligne pour le prix moyen global
    global_mean = df['prix'].mean()
    ax.axhline(y=global_mean, color='red', linestyle='--', alpha=0.7, 
               label=f'Prix Moyen Global: {global_mean:.2f}€')
    ax.legend()
    
    plt.tight_layout()
    return fig

def plot_sentiment_vs_price(df, top_n=8):
    """
    Scatter plot sentiment vs prix avec marques colorées
    
    Args:
        df: DataFrame
        top_n: Nombre de marques à afficher distinctement
    
    Returns:
        plotly.graph_objects.Figure: Figure Plotly interactive
    """
    # Sélectionner les top N marques
    top_brands = df['brand'].value_counts().head(top_n).index
    df_plot = df.copy()
    
    # Créer une colonne pour le groupe (top brands vs autres)
    df_plot['brand_group'] = df_plot['brand'].apply(
        lambda x: x if x in top_brands else 'Autres marques'
    )
    
    # Utiliser nb_avis si disponible, sinon une taille fixe
    size_col = 'nb_avis' if 'nb_avis' in df.columns else None
    
    fig = px.scatter(
        df_plot,
        x='sentiment_score',
        y='prix',
        color='brand_group',
        size=size_col,
        hover_data=['titre', 'note', 'category'],
        title='Relation entre Sentiment Client et Prix',
        labels={
            'sentiment_score': 'Score de Sentiment (1-5)',
            'prix': 'Prix (€)',
            'brand_group': 'Marque'
        },
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    # Ajouter une ligne de régression
    z = np.polyfit(df['sentiment_score'].dropna(), df['prix'].dropna(), 1)
    p = np.poly1d(z)
    
    x_range = np.linspace(df['sentiment_score'].min(), df['sentiment_score'].max(), 100)
    fig.add_trace(
        go.Scatter(
            x=x_range,
            y=p(x_range),
            mode='lines',
            name='Tendance',
            line=dict(color='red', dash='dash'),
            showlegend=True
        )
    )
    
    fig.update_layout(
        height=600,
        hovermode='closest',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    return fig

def plot_brand_positioning(df):
    """
    Bubble chart pour le positionnement des marques (prix moyen vs sentiment moyen)
    
    Args:
        df: DataFrame
    
    Returns:
        plotly.graph_objects.Figure: Figure Plotly
    """
    # Calcul des moyennes par marque
    brand_stats = df.groupby('brand').agg({
        'prix': 'mean',
        'sentiment_score': 'mean',
        'note': 'mean',
        'titre': 'count'
    }).rename(columns={'titre': 'nombre_produits'}).reset_index()
    
    # Filtrer les marques avec suffisamment de produits
    brand_stats = brand_stats[brand_stats['nombre_produits'] >= 3]
    
    fig = px.scatter(
        brand_stats,
        x='sentiment_score',
        y='prix',
        size='nombre_produits',
        color='note',
        hover_name='brand',
        hover_data=['nombre_produits', 'note'],
        title='Positionnement des Marques: Prix Moyen vs Sentiment Moyen',
        labels={
            'sentiment_score': 'Sentiment Moyen (1-5)',
            'prix': 'Prix Moyen (€)',
            'note': 'Note Moyenne',
            'nombre_produits': 'Nombre de Produits'
        },
        color_continuous_scale='RdYlGn'
    )
    
    # Ajouter des quadrants
    avg_price = brand_stats['prix'].mean()
    avg_sentiment = brand_stats['sentiment_score'].mean()
    
    fig.add_hline(y=avg_price, line_dash="dash", line_color="gray", 
                  annotation_text="Prix Moyen", annotation_position="top right")
    fig.add_vline(x=avg_sentiment, line_dash="dash", line_color="gray",
                  annotation_text="Sentiment Moyen", annotation_position="top right")
    
    # Ajouter des annotations pour les quadrants
    annotations = [
        dict(x=avg_sentiment * 0.7, y=avg_price * 1.3, 
             text="Marques Premium", showarrow=False, font=dict(color="green")),
        dict(x=avg_sentiment * 1.3, y=avg_price * 1.3, 
             text="Marques Excellentes", showarrow=False, font=dict(color="darkgreen")),
        dict(x=avg_sentiment * 0.7, y=avg_price * 0.7, 
             text="Marques Économiques", showarrow=False, font=dict(color="orange")),
        dict(x=avg_sentiment * 1.3, y=avg_price * 0.7, 
             text="Meilleur Rapport Q/P", showarrow=False, font=dict(color="red"))
    ]
    
    fig.update_layout(
        height=700,
        annotations=annotations,
        coloraxis_colorbar=dict(title="Note Moyenne")
    )
    
    return fig

def plot_sentiment_distribution(df):
    """
    Distribution des scores de sentiment
    
    Args:
        df: DataFrame
    
    Returns:
        matplotlib.figure.Figure: Figure matplotlib
    """
    setup_plot_style()
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Histogramme
    axes[0].hist(df['sentiment_score'].dropna(), bins=20, alpha=0.7, color='skyblue', edgecolor='black')
    axes[0].axvline(df['sentiment_score'].mean(), color='red', linestyle='--', 
                    linewidth=2, label=f'Moyenne: {df["sentiment_score"].mean():.2f}')
    axes[0].set_title('Distribution des Scores de Sentiment', fontsize=16, fontweight='bold')
    axes[0].set_xlabel('Score de Sentiment (1-5)', fontsize=14)
    axes[0].set_ylabel('Fréquence', fontsize=14)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Boxplot par marque (top 8)
    top_brands = df['brand'].value_counts().head(8).index
    df_brands = df[df['brand'].isin(top_brands)]
    
    brand_order = df_brands.groupby('brand')['sentiment_score'].mean().sort_values(ascending=False).index
    
    sns.boxplot(data=df_brands, x='brand', y='sentiment_score', 
                order=brand_order, ax=axes[1], palette='coolwarm')
    axes[1].set_title('Scores de Sentiment par Marque (Top 8)', fontsize=16, fontweight='bold')
    axes[1].set_xlabel('Marque', fontsize=14)
    axes[1].set_ylabel('Score de Sentiment', fontsize=14)
    axes[1].tick_params(axis='x', rotation=45)
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

def plot_price_vs_features(df):
    """
    Analyse multivariée des prix
    
    Args:
        df: DataFrame
    
    Returns:
        matplotlib.figure.Figure: Figure matplotlib
    """
    setup_plot_style()
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()
    
    # 1. Prix vs Note
    scatter1 = axes[0].scatter(df['note'], df['prix'], alpha=0.6, c=df['sentiment_score'], 
                               cmap='viridis', s=50)
    axes[0].set_title('Prix vs Note (couleur = sentiment)', fontsize=14, fontweight='bold')
    axes[0].set_xlabel('Note Client', fontsize=12)
    axes[0].set_ylabel('Prix (€)', fontsize=12)
    plt.colorbar(scatter1, ax=axes[0]).set_label('Score de Sentiment', rotation=270, labelpad=15)
    
    # 2. Prix vs Nombre d'avis
    axes[1].scatter(df['nombre_avis'], df['prix'], alpha=0.6, color='teal', s=50)
    axes[1].set_title('Prix vs Nombre d\'Avis', fontsize=14, fontweight='bold')
    axes[1].set_xlabel('Nombre d\'Avis', fontsize=12)
    axes[1].set_ylabel('Prix (€)', fontsize=12)
    axes[1].set_xscale('log')  # Échelle logarithmique pour mieux voir
    
    # 3. Distribution des prix par catégorie (top 5)
    top_categories = df['category'].value_counts().head(5).index
    df_cat = df[df['category'].isin(top_categories)]
    
    for i, category in enumerate(top_categories):
        cat_data = df_cat[df_cat['category'] == category]['prix'].dropna()
        axes[2].hist(cat_data, bins=20, alpha=0.5, label=category)
    
    axes[2].set_title('Distribution des Prix par Catégorie (Top 5)', fontsize=14, fontweight='bold')
    axes[2].set_xlabel('Prix (€)', fontsize=12)
    axes[2].set_ylabel('Fréquence', fontsize=12)
    axes[2].legend()
    
    # 4. Corrélation heatmap
    numeric_cols = ['prix', 'note', 'nombre_avis', 'sentiment_score']
    corr_data = df[numeric_cols].corr()
    
    im = axes[3].imshow(corr_data, cmap='coolwarm', vmin=-1, vmax=1)
    axes[3].set_title('Matrice de Corrélation', fontsize=14, fontweight='bold')
    axes[3].set_xticks(range(len(numeric_cols)))
    axes[3].set_yticks(range(len(numeric_cols)))
    axes[3].set_xticklabels(numeric_cols, rotation=45)
    axes[3].set_yticklabels(numeric_cols)
    
    # Ajouter les valeurs de corrélation
    for i in range(len(numeric_cols)):
        for j in range(len(numeric_cols)):
            text = axes[3].text(j, i, f'{corr_data.iloc[i, j]:.2f}',
                           ha="center", va="center", color="black", fontsize=10)
    
    plt.colorbar(im, ax=axes[3]).set_label('Corrélation', rotation=270, labelpad=15)
    
    plt.tight_layout()
    return fig