

import streamlit as st
import pandas as pd
import json
import plotly.express as px
import os
import re

st.set_page_config(
    page_title="📊 Visualisation Udemy IA",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_PATH = "/home/mohamed/Bureau/global_dataset.json" # Attention: ce chemin est spécifique à l'environnement d'origine.

@st.cache_data(show_spinner="Chargement des données Udemy (cours + certificats)...")
def load_data(json_path):
    """
    Charge le JSON, crée un DataFrame, ajoute/normalise les colonnes importantes :
      - price_numeric  (float)
      - description    (str)
      - type (“Cours” / “Certificat”)
    """
    # Note: Le chemin DATA_PATH est codé en dur. Pour une meilleure portabilité,
    # il pourrait être préférable de le rendre configurable ou relatif.
    if not os.path.exists(json_path):
        st.error(f"🚨 Le fichier `{json_path}` est introuvable. Assurez-vous que le chemin est correct pour votre environnement.")
        st.stop()

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
    except Exception as e:
        st.error(f"🚨 Erreur lors de la lecture du fichier JSON : {e}")
        st.stop()

    df = pd.DataFrame(raw)

    def parse_price(x):
        if isinstance(x, (int, float)):
            return float(x)
        s = str(x).lower().strip()
        if s in ["free", "gratuit", "0", "0.0", "null", "none", ""]:
            return 0.0
        num = re.sub(r"[^\d\.]", "", s)
        try:
            return float(num)
        except:
            return 0.0

    df["price_numeric"] = df.get("current_price", 0).apply(parse_price)
    df["description"] = df.get("description", "").fillna("").astype(str)

    def infer_type(row):
        cat = str(row.get("category", "")).lower()
        title = str(row.get("title", "")).lower()
        if "certif" in cat or "certificate" in cat or "certificat" in cat:
            return "Certificat"
        if any(keyword in title for keyword in ["certificate", "certificat", "aws certified"]):
            return "Certificat"
        return "Cours"

    df["type"] = df.apply(infer_type, axis=1)

    for col in ["category", "level", "language"]:
        df[col] = df.get(col, "Inconnu").fillna("Inconnu").astype(str)

    # Ajout de colonnes si elles existent dans le JSON original, sinon NaN
    for col in ["students_enrolled", "rating", "duration_hours"]:
        if col not in df.columns:
             df[col] = pd.NA # Ou une autre valeur par défaut comme 0 ou np.nan si numpy est importé
        else:
             # Tentative de conversion en numérique, gestion des erreurs
             df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

df = load_data(DATA_PATH)

def page_exploration(df: pd.DataFrame):
    """
    Affiche l'Exploration des Données avec filtres :
      - Type : Tous / Cours / Certificats
      - Catégorie
      - Niveau
      - Fourchette de prix
    Puis génère plusieurs graphiques Plotly pour :
      • Répartition par catégorie
      • Répartition par niveau
      • Distribution des prix
      • Corrélations, etc.
    """

    st.title("🔍 Exploration des Données Udemy IA (Cours + Certificats)")

    with st.sidebar.expander("🔧 Filtres EDA", expanded=True):
        type_options = ["Tous", "Cours", "Certificat"]
        select_type = st.selectbox("Sélectionner le Type", type_options, index=0)

        cats = sorted(df["category"].unique())
        cats.insert(0, "Tous")
        select_cat = st.selectbox("Filtrer par Catégorie", cats, index=0)

        levels = sorted(df["level"].unique())
        levels.insert(0, "Tous")
        select_level = st.selectbox("Filtrer par Niveau", levels, index=0)

        min_price = float(df["price_numeric"].min())
        max_price = float(df["price_numeric"].max())
        # Assurer que min_value n'est pas supérieur à max_value
        if min_price > max_price:
            min_price = max_price
        price_range = st.slider(
            "Fourchette de Prix (€)",
            min_value=round(min_price, 2),
            max_value=round(max_price, 2),
            value=(round(min_price, 2), round(max_price, 2))
        )

    df_eda = df.copy()

    if select_type != "Tous":
        df_eda = df_eda[df_eda["type"] == select_type]

    if select_cat != "Tous":
        df_eda = df_eda[df_eda["category"] == select_cat]

    if select_level != "Tous":
        df_eda = df_eda[df_eda["level"] == select_level]

    df_eda = df_eda[
        (df_eda["price_numeric"] >= price_range[0]) &
        (df_eda["price_numeric"] <= price_range[1])
    ]

    if df_eda.empty:
        st.warning("⚠️ Aucun enregistrement ne correspond aux filtres sélectionnés.")
        st.stop()

    st.markdown(f"**Nombre d’enregistrements affichés : {len(df_eda)}**")

    st.subheader("📄 Statistiques descriptives")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Moyenne Prix (€)", f"{df_eda['price_numeric'].mean():.2f}")
        st.metric("Médiane Prix (€)", f"{df_eda['price_numeric'].median():.2f}")
    with col2:
        st.metric("Prix Min (€)", f"{df_eda['price_numeric'].min():.2f}")
        st.metric("Prix Max (€)", f"{df_eda['price_numeric'].max():.2f}")
    with col3:
        st.metric("Écart-type Prix", f"{df_eda['price_numeric'].std():.2f}")
        st.metric("Nombre Catégories Distinctes", f"{df_eda['category'].nunique()}")

    st.markdown("---")

    st.subheader("Figure 4.1 – Histogramme de la distribution des prix")
    fig_price = px.histogram(
        df_eda,
        x="price_numeric",
        nbins=50,
        title="Distribution des Prix",
        labels={"price_numeric": "Prix (€)"},
        color_discrete_sequence=["#636EFA"]
    )
    fig_price.update_layout(margin=dict(t=40, b=20, l=20, r=20))
    st.plotly_chart(fig_price, use_container_width=True)

    st.subheader("Figure 4.2 – Boîtes à moustaches des prix par Type")
    fig_box_type = px.box(
        df_eda,
        x="type",
        y="price_numeric",
        title="Prix par Type",
        labels={"type": "Type", "price_numeric": "Prix (€)"},
        color="type",
        color_discrete_map={"Cours": "#EF553B", "Certificat": "#00CC96"}
    )
    fig_box_type.update_layout(showlegend=False, margin=dict(t=40, b=20, l=20, r=20))
    st.plotly_chart(fig_box_type, use_container_width=True)

    if "students_enrolled" in df_eda.columns and not df_eda["students_enrolled"].isnull().all():
        st.subheader("Figure 4.3 – Relation entre le nombre d’inscrits et le prix")
        fig_scatter = px.scatter(
            df_eda.dropna(subset=["students_enrolled", "price_numeric"]),
            x="students_enrolled",
            y="price_numeric",
            title="Nombre d’inscrits vs Prix",
            labels={"students_enrolled": "Nombre d’inscrits", "price_numeric": "Prix (€)"},
            color="type",
            color_discrete_map={"Cours": "#636EFA", "Certificat": "#AB63FA"},
            hover_data=["title"]
        )
        fig_scatter.update_layout(margin=dict(t=40, b=20, l=20, r=20))
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("ℹ️ Données `students_enrolled` non disponibles ou incomplètes pour tracer la Figure 4.3.")

    st.subheader("Figure 4.4 – Matrice de corrélation (heatmap)")
    numeric_cols = df_eda.select_dtypes(include=['number']).columns.tolist()
    # Exclure les identifiants ou colonnes non pertinentes si nécessaire
    numeric_cols = [col for col in numeric_cols if col not in ['id', 'some_other_non_numeric_id']]

    if len(numeric_cols) >= 2:
        corr = df_eda[numeric_cols].corr()
        fig_corr = px.imshow(
            corr,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="RdBu_r",
            title="Corrélations (Numériques)"
        )
        fig_corr.update_layout(margin=dict(t=40, b=20, l=20, r=20))
        st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.info("ℹ️ Pas assez de colonnes numériques (>1) pour tracer la Figure 4.4.")

    st.markdown("---")

    st.subheader("Aperçu tabulaire (50 premières lignes)")
    st.dataframe(df_eda.head(50), use_container_width=True)

def main():
    # La navigation est retirée car il n'y a plus qu'une seule page
    st.sidebar.title("📊 Visualisation")
    st.sidebar.info("Utilisez les filtres ci-dessus pour explorer les données.")
    page_exploration(df)

if __name__ == "__main__":
    main()

