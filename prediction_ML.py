# fichier : app_pricing_evaluation.py

import streamlit as st
import json
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error, max_error
from sentence_transformers import SentenceTransformer
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import os

# === PARAMÈTRES ===
DATA_PATH = "/home/mohamed/Bureau/all.json"
MODEL_PATH = "./price_predictor.joblib"
EMBEDDINGS_PATH = "./embeddings.npy"
BATCH_SIZE = 8

# Nettoyage robuste des prix
def clean_price(price):
    if price in ['free', 'null', '', None]:
        return 0.0
    try:
        return float(price)
    except:
        return 0.0

# Chargement des données
@st.cache_data
def load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    df['price'] = df['current_price'].apply(clean_price)
    df['fulltext'] = df['title'].fillna('') + " " + df['description'].fillna('')
    return df

# Chargement du modèle de embeddings
@st.cache_resource
def load_embedder():
    return SentenceTransformer("all-MiniLM-L6-v2")

# Préparation et sauvegarde des embeddings
@st.cache_resource
def prepare_embeddings(df):
    embedder = load_embedder()
    embeddings = embedder.encode(df['fulltext'].tolist(), batch_size=BATCH_SIZE, show_progress_bar=True)
    np.save(EMBEDDINGS_PATH, embeddings)
    return embeddings

# Entrainement et sauvegarde du modèle
@st.cache_resource
def train_model(embeddings, prices):
    X_train, X_test, y_train, y_test = train_test_split(embeddings, prices, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)
    joblib.dump(model, MODEL_PATH)
    return model, X_test, y_test

# === STREAMLIT UI ===
st.title("💰 Prédiction et Évaluation avancée de Prix IA (Cours & Certificats)")
data = load_data()

# Préparer embeddings et modèle
if not os.path.exists(EMBEDDINGS_PATH):
    st.info("💾 Calcul des embeddings...")
    embeddings = prepare_embeddings(data)
else:
    embeddings = np.load(EMBEDDINGS_PATH)

if not os.path.exists(MODEL_PATH):
    st.info("🔧 Entrainement du modèle...")
    model, X_test, y_test = train_model(embeddings, data['price'].values)
else:
    model = joblib.load(MODEL_PATH)
    X_train, X_test, y_train, y_test = train_test_split(embeddings, data['price'].values, test_size=0.2, random_state=42)

# ÉVALUATION AVANCÉE

y_pred = model.predict(X_test)
r2 = r2_score(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
max_err = max_error(y_test, y_pred)

st.subheader("📊 Évaluation avancée du modèle :")
st.write(f"✅ Coefficient R² : **{r2*100:.2f}%**")
st.write(f"✅ MAE (Erreur absolue moyenne) : **{mae:.2f} €**")
st.write(f"✅ RMSE (Erreur quadratique moyenne) : **{rmse:.2f} €**")
st.write(f"✅ Max Error : **{max_err:.2f} €**")

# Courbe prix réel vs prix prédit
st.subheader("📈 Courbe Prix Réel vs Prix Prédit")

plt.figure(figsize=(8,6))
sns.scatterplot(x=y_test, y=y_pred, color='blue', alpha=0.6)
plt.plot([0, max(y_test)], [0, max(y_test)], color='red', linestyle='--')
plt.xlabel("Prix Réel (€)")
plt.ylabel("Prix Prédit (€)")
plt.title("Comparaison des Prix Réels et Prédits")
st.pyplot(plt)

# Distribution des erreurs
st.subheader("📉 Distribution des erreurs de prédiction")

errors = y_test - y_pred
plt.figure(figsize=(8,5))
sns.histplot(errors, bins=30, kde=True, color='skyblue')
plt.axvline(0, color='red', linestyle='--')
plt.title("Distribution des erreurs (Prix Réel - Prédit)")
plt.xlabel("Erreur (€)")
plt.ylabel("Fréquence")
st.pyplot(plt)

# Interface de prédiction pour l'utilisateur

st.header("📊 Tester une nouvelle prédiction de prix")

title = st.text_input("Titre du cours :")
description = st.text_area("Description du cours :")

if st.button("Prédire le prix sur ce nouveau cours"):
    if not title or not description:
        st.warning("⚠️ Entrez un titre et une description avant de prédire.")
    else:
        embedder = load_embedder()
        new_text = title + " " + description
        new_embed = embedder.encode([new_text])
        predicted_price = model.predict(new_embed)[0]
        st.success(f"💰 Prix estimé : {predicted_price:.2f} €")
