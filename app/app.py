"""
Application principale Streamlit - Analyse E-commerce
Avec CSS personnalisé
"""

import streamlit as st
import os
from pathlib import Path
import pandas as pd

# ===== CHARGEMENT DU CSS =====
def load_css():
    """Charge le CSS personnalisé"""
    css_path = Path(__file__).parent / "styles.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    else:
        # CSS par défaut si le fichier n'existe pas
        default_css = """
        <style>
        .stApp { background-color: #f8f9fa; }
        h1 { color: #1e3a8a; }
        </style>
        """
        st.markdown(default_css, unsafe_allow_html=True)

# ===== CONFIGURATION DE LA PAGE =====
st.set_page_config(
    page_title="Analyse E-commerce - Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Charger le CSS
load_css()

# ===== FONCTIONS UTILITAIRES =====
# ===== HEADER AVEC STYLE =====
st.markdown("""
<div style="text-align: center; padding: 2rem 0; background: linear-gradient(90deg, #1e3a8a, #3b82f6); 
            border-radius: 10px; margin-bottom: 2rem;">
    <h1 style="color: white; margin-bottom: 0.5rem;">📊 Dashboard d'Analyse E-commerce</h1>
    <p style="color: rgba(255,255,255,0.9); font-size: 1.1rem; max-width: 800px; margin: 0 auto;">
    <strong>Analyse concurrentielle entre marques</strong> - Samsung, Apple, Xiaomi, etc.
    <br>Données extraites d'Amazon et Jumia •
    </p>
</div>
""", unsafe_allow_html=True)

# ===== SIDEBAR STYLÉE =====
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <div style="font-size: 3rem; color: white;">📈</div>
        <h2 style="color: white; margin-top: 0.5rem;">Navigation</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Navigation avec badges
    pages = {
        "📊 Dashboard Global": "1_dashboard",
        "💰 Prix vs Marques": "2_prix", 
        "😊 NLP & Sentiments": "3_sentiment",
        "🎯 Recommandations": "4_reco"
    }
    
    for page_name, page_file in pages.items():
        if st.button(f"**{page_name}**", width='stretch', type="primary"):
            st.switch_page(f"pages/{page_file}.py")
    
    st.markdown("---")
    
    # Section informations
    st.markdown("""
    <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px; margin: 1rem 0;">
        <h3 style="color: white; margin-bottom: 0.5rem;">ℹ️ Informations</h3>
        <p style="color: rgba(255,255,255,0.9); font-size: 0.9rem;">
        <strong>Contexte du projet:</strong><br>
        • Web scraping Amazon & Jumia<br>
        • Analyse NLP avec Transformers<br>
        • Clustering textuel<br>
        • Prédiction de prix
        </p>
    </div>
    """, unsafe_allow_html=True)

# ===== CONTENU PRINCIPAL =====
try:
    from utils.load_data import load_processed_data
    df = load_processed_data()
    
    if not df.empty:
        # Cartes de bienvenue stylées
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="custom-card">
                <div class="custom-card-header">
                    <span class="custom-card-icon">🎯</span>
                    <h3 class="custom-card-title">Objectif Principal</h3>
                </div>
                <div class="custom-card-content">
                    Analyse comparative des <strong>stratégies de pricing</strong> et 
                    <strong>perception client</strong> entre marques concurrentes.
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="custom-card">
                <div class="custom-card-header">
                    <span class="custom-card-icon">📊</span>
                    <h3 class="custom-card-title">Couverture Données</h3>
                </div>
                <div class="custom-card-content">
                    <strong>{len(df)} produits</strong> analysés<br>
                    <strong>{df['brand'].nunique()} marques</strong> comparées<br>
                    Données combinées Amazon & Jumia
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="custom-card">
                <div class="custom-card-header">
                    <span class="custom-card-icon">🤖</span>
                    <h3 class="custom-card-title">Technologie</h3>
                </div>
                <div class="custom-card-content">
                    NLP avancé avec <strong>Transformers</strong><br>
                    Visualisations interactives<br>
                    Algorithmes de recommandation
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Section d'introduction
        st.markdown("---")
        
        intro_cols = st.columns(2)
        
        with intro_cols[0]:
            st.markdown("""
            <div style="background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="color: #1e3a8a; border-bottom: 2px solid #3b82f6; padding-bottom: 0.5rem;">
                    🔍 Analyse Concurrentielle
                </h3>
                <ul style="color: #374151; line-height: 2;">
                    <li><strong>Comparaison des prix</strong> entre marques</li>
                    <li><strong>Positionnement marché</strong> et stratégies</li>
                    <li>Identification des <strong>opportunités</strong></li>
                    <li>Analyse <strong>sentiment vs pricing</strong></li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with intro_cols[1]:
            st.markdown("""
            <div style="background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="color: #1e3a8a; border-bottom: 2px solid #10b981; padding-bottom: 0.5rem;">
                    📈 Insights Actionnables
                </h3>
                <ul style="color: #374151; line-height: 2;">
                    <li>Produits <strong>sous/sur-évalués</strong></li>
                    <li>Recommandations <strong>stratégiques</strong></li>
                    <li>Analyse <strong>data-driven</strong></li>
                    <li>Visualisations <strong>professionnelles</strong></li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Instructions
        with st.expander("📋 Comment utiliser cette application", expanded=False):
            st.markdown("""
            <div style="padding: 1rem;">
                <h4>🎯 Navigation</h4>
                <ol style="color: #374151; line-height: 1.8;">
                    <li><strong>Dashboard Global</strong> : Vue d'ensemble avec KPIs et filtres</li>
                    <li><strong>Analyse Prix vs Marques</strong> : Comparaison concurrentielle détaillée</li>
                    <li><strong>Analyse NLP & Sentiments</strong> : Perception client et scores de sentiment</li>
                    <li><strong>Recommandations</strong> : Produits à fort potentiel selon plusieurs critères</li>
                </ol>
                
                <div style="background: #f0f9ff; padding: 1rem; border-radius: 8px; margin: 1rem 0; border-left: 4px solid #3b82f6;">
                    <strong>⚠️ Important :</strong> L'analyse se concentre sur la concurrence entre <strong>marques</strong>, 
                    pas entre plateformes (Amazon vs Jumia).
                </div>
                
                <h4>🎓 Valeur Académique</h4>
                <p style="color: #374151;">
                Cette application démontre une approche professionnelle d'analyse de données e-commerce :
                </p>
                <ul style="color: #374151; line-height: 1.8;">
                    <li>Méthodologie rigoureuse</li>
                    <li>Visualisations interactives</li>
                    <li>Insights basés sur les données</li>
                    <li>Interface utilisateur intuitive</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
    else:
        st.error("""
        <div style="text-align: center; padding: 2rem;">
            <h2 style="color: #dc2626;">⚠️ Données non chargées</h2>
            <p>Vérifiez que le fichier <code>data/processed/final_products.csv</code> existe et contient des données.</p>
        </div>
        """, unsafe_allow_html=True)
        
except Exception as e:
    st.markdown(f"""
    <div style="background: #fee2e2; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #dc2626;">
        <h3 style="color: #991b1b; margin-top: 0;">❌ Erreur de chargement</h3>
        <p style="color: #7f1d1d;"><strong>Détails :</strong> {str(e)}</p>
        <p style="color: #7f1d1d;">Vérifiez la structure de vos données ou exécutez le script de debug.</p>
    </div>
    """)

# ===== FOOTER STYLÉ =====
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6b7280; padding: 1rem 0; font-size: 0.9rem;">
    <p><strong>Projet - Analyse E-commerce</strong></p>
    <p>Technologies : Streamlit • Pandas • Seaborn • Matplotlib • Plotly • NLP Transformers</p>
    <p style="margin-top: 0.5rem;">
        <span class="badge badge-primary">Version 1.0</span>
        <span class="badge badge-success" style="margin-left: 0.5rem;">Production</span>
        <span class="badge badge-warning" style="margin-left: 0.5rem;">Académique</span>
    </p>
</div>
""", unsafe_allow_html=True)

# ===== SCRIPT JS POUR ANIMATIONS SUPPLEMENTAIRES =====
st.markdown("""
<script>
// Animation pour les cartes
document.addEventListener('DOMContentLoaded', function() {
    // Observer pour les animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Appliquer aux cartes
    document.querySelectorAll('.custom-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(card);
    });
});
</script>
""", unsafe_allow_html=True)