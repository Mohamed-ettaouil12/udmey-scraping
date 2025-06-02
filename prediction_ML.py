# -*- coding: utf-8 -*-
"""
app_visualisation.py

Streamlit : Visualisation Exploratoire des Données Udemy IA (Cours + Certificats)

Affiche :
 - Figure 4.1 : Histogramme de la distribution des prix
 - Figure 4.2 : Boîtes à moustaches des prix par type (Cours vs Certificats)
 - Figure 4.3 : Relation prix vs nombre d'inscrits (scatter plot)
 - Figure 4.4 : Matrice de corrélation (heatmap) sur variables numériques
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

                                                                       
                           
                                                                       
st.set_page_config(
    page_title="🔎 EDA Udemy IA (Cours + Certificats)",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_PATH = "/home/mohamed/Bureau/global_dataset.json"                                      

                                                                       
                                                
                                                                       
@st.cache_data(show_spinner=False)
def load_and_clean_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        st.error(f"Le fichier JSON n'a pas été trouvé :\n    {path}")
        return pd.DataFrame()

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        st.error(f"Impossible de lire le JSON : {e}")
        return pd.DataFrame()

    df = pd.DataFrame(data)

                                    
    def clean_price(x):
        if x is None:
            return 0.0
        if isinstance(x, str):
            s = x.strip().lower()
            if s in ("free", "null", ""):
                return 0.0
            s = s.replace("€", "").replace(",", ".").replace(" ", "")
            try:
                return float(s)
            except:
                return 0.0
        try:
            return float(x)
        except:
            return 0.0

    if "current_price" not in df.columns:
        st.warning("La colonne 'current_price' est absente. Remplissage à 0.0.")
        df["price"] = 0.0
    else:
        df["price"] = df["current_price"].apply(clean_price)

                                    
    if "students_enrolled" in df.columns:
        df["students_enrolled"] = pd.to_numeric(
            df["students_enrolled"], errors="coerce"
        ).fillna(0).astype(int)
    else:
                                                                 
        df["students_enrolled"] = 0

                                                         
                                                            
                                                 
    numeric_cols = ["rating", "num_reviews", "duration"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        else:
            df[col] = 0.0

                                                           
                                                              
    for col in ["category", "level", "title", "description"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)
        else:
            df[col] = ""

                                                                    
    def classify_type(cat: str) -> str:
        cat_lower = cat.lower()
                                                                                                                
        if "certified" in cat_lower:
            return "Certificat"
                                               
        return "Cours"

    df["Type"] = df["category"].apply(classify_type)

    return df


                                                                       
                    
                                                                       
def main():
    st.title("🔎 Exploration des Données Udemy IA (Cours + Certificats)")

    df = load_and_clean_data(DATA_PATH)
    if df.empty:
        st.stop()

                                                      
    st.sidebar.header("Filtres EDA")
    types_list = ["Tous"] + sorted(df["Type"].unique().tolist())
    type_filter = st.sidebar.selectbox("Type", types_list, index=0)

    cats = ["Tous"] + sorted(df["category"].unique().tolist())
    cat_filter = st.sidebar.selectbox("Catégorie", cats, index=0)

    lvls = ["Tous"] + sorted(df["level"].unique().tolist())
    level_filter = st.sidebar.selectbox("Niveau", lvls, index=0)

                           
    df_filtered = df.copy()
    if type_filter != "Tous":
        df_filtered = df_filtered[df_filtered["Type"] == type_filter]
    if cat_filter != "Tous":
        df_filtered = df_filtered[df_filtered["category"] == cat_filter]
    if level_filter != "Tous":
        df_filtered = df_filtered[df_filtered["level"] == level_filter]

    st.markdown(f"- Nombre d’enregistrements affichés : **{len(df_filtered):,}**")

                                                                       
                                                               
                                                                       
    st.subheader("Figure 4.1 – Histogramme de la distribution des prix")
    fig1, ax1 = plt.subplots(figsize=(8, 4))
    sns.histplot(
        df_filtered["price"],
        bins=50,
        kde=True,
        color="slateblue",
        edgecolor="white",
        alpha=0.75,
        ax=ax1,
    )
    ax1.set_xlabel("Prix (€)")
    ax1.set_ylabel("Nombre de cours+certificats")
    ax1.set_title("Distribution des prix (Cours + Certificats)")
    plt.tight_layout()
    st.pyplot(fig1)

                                                                       
                                                             
                                                                       
    st.subheader("Figure 4.2 – Boîtes à moustaches des prix par Type")
    fig2, ax2 = plt.subplots(figsize=(7, 4))
    sns.boxplot(
        x="Type",
        y="price",
        data=df_filtered,
        palette={"Cours": "tomato", "Certificat": "mediumseagreen"},
        ax=ax2,
    )
    ax2.set_xlabel("Type")
    ax2.set_ylabel("Prix (€)")
    ax2.set_title("Prix par Type : Cours vs Certificat")
    plt.tight_layout()
    st.pyplot(fig2)

                                                                       
                                                                   
                                                                       
    st.subheader("Figure 4.3 – Relation entre le nombre d’inscrits et le prix")
    fig3, ax3 = plt.subplots(figsize=(7, 4))
                                                                     
    sns.scatterplot(
        x="students_enrolled",
        y="price",
        data=df_filtered,
        hue="Type",
        palette={"Cours": "tomato", "Certificat": "mediumseagreen"},
        alpha=0.6,
        ax=ax3,
    )
    ax3.set_xscale("log")
    ax3.set_xlabel("Nombre d’inscrits (log)")
    ax3.set_ylabel("Prix (€)")
    ax3.set_title("Nombre d’inscrits vs Prix")
    ax3.legend(title="Type")
    plt.tight_layout()
    st.pyplot(fig3)

                                                                       
                                                        
                                                                       
    st.subheader("Figure 4.4 – Matrice de corrélation (features numériques)")
                                                                  
    num_cols = ["price", "students_enrolled"]
                                                     
    if "rating" in df_filtered.columns:
        num_cols.append("rating")
    if "num_reviews" in df_filtered.columns:
        num_cols.append("num_reviews")
    if "duration" in df_filtered.columns:
        num_cols.append("duration")

    corr_df = df_filtered[num_cols].copy()
    corr_mat = corr_df.corr()

    fig4, ax4 = plt.subplots(figsize=(5, 4))
    sns.heatmap(
        corr_mat,
        annot=True,
        fmt=".2f",
        cmap="RdBu_r",
        linewidths=0.5,
        cbar_kws={"shrink": 0.7},
        ax=ax4,
    )
    ax4.set_title("Matrice de corrélation")
    plt.tight_layout()
    st.pyplot(fig4)

                                                                       
                                                                   
                                                                       
    st.markdown("----")
    st.subheader("Aperçu des données filtrées")
    st.dataframe(df_filtered.head(10), use_container_width=True)


if __name__ == "__main__":
    main()
