                  

import streamlit as st
import json
import chromadb
from sentence_transformers import SentenceTransformer
import os

                                  
JSON_PATH = '/home/mohamed/Bureau/global_dataset.json'                                          
CHROMA_PATH = "./chromadb-tawilpfa-docs"                                                           

                                                                          

@st.cache_resource
def load_model():
    """
    Charge le modèle SentenceTransformer, en essayant d'utiliser CUDA si disponible,
    sinon en se rabattant sur le CPU.
    """
    try:
                                             
        model = SentenceTransformer('all-MiniLM-L6-v2', device='cuda')
        st.success("✅ Modèle SentenceTransformer chargé sur CUDA (GPU).")
        return model
    except Exception as e:
                                        
        st.warning(f"⚠️ CUDA indisponible ou erreur lors du chargement sur GPU: {e}. Passage sur CPU.")
        return SentenceTransformer('all-MiniLM-L6-v2', device='cpu')

@st.cache_data
def load_json():
    """
    Charge les données depuis le fichier JSON spécifié.
    """
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        st.success(f"✅ Données JSON chargées depuis '{JSON_PATH}'.")
        return data
    except FileNotFoundError:
        st.error(f"❌ Erreur: Le fichier JSON '{JSON_PATH}' est introuvable. Veuillez vérifier le chemin.")
        st.stop()                                                                     
    except json.JSONDecodeError:
        st.error(f"❌ Erreur: Impossible de décoder le fichier JSON '{JSON_PATH}'. Vérifiez sa syntaxe.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Une erreur inattendue est survenue lors du chargement du JSON: {e}")
        st.stop()

@st.cache_resource
def initialize_chroma(data):
    """
    Initialise ou réinitialise la collection ChromaDB, ajoute les documents et leurs embeddings.
    Gère la suppression de la collection existante pour un démarrage propre.
    """
    st.info("🚀 Initialisation de ChromaDB...")
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    
                                                                          
    try:
        client.delete_collection("courses_collection")
        st.info("🔄 Collection 'courses_collection' existante supprimée pour re-création.")
    except chromadb.errors.NotFoundError:
        st.info("➕ Collection 'courses_collection' n'existe pas encore. Création en cours.")
    except Exception as e:
        st.error(f"❌ Erreur inattendue lors de la tentative de suppression de la collection: {e}")
        st.stop()

                                                                                                       
    collection = client.create_collection(name="courses_collection")
    st.success("✅ Collection 'courses_collection' prête.")

    docs, ids, metas = [], [], []
    model = load_model()                                                     

                                                                          
    for idx, record in enumerate(data):
                                                               
        title = str(record.get('title', ''))
        description = str(record.get('description', ''))
        
                                                                                 
        what_you_will_learn_list = record.get('what_you_will_learn')
        if isinstance(what_you_will_learn_list, list):
            what_you_learn_str = " ".join(map(str, what_you_will_learn_list))
        elif what_you_will_learn_list is not None:
            what_you_learn_str = str(what_you_will_learn_list)
        else:
            what_you_learn_str = ""

        combined_text = f"{title} {description} {what_you_learn_str}"
        docs.append(combined_text)
        ids.append(str(idx))

                                                                   
        clean_meta = {}
        for k, v in record.items():
                                                                         
            if isinstance(v, (str, int, float, bool)):
                clean_meta[k] = v
            elif isinstance(v, list):
                                                                      
                clean_meta[k] = " / ".join(map(str, v))
            elif v is None:
                                                                                              
                clean_meta[k] = ""
                                                                               
                                                                                        
                                                                                                   
                                               

                                                                                                      
        try:
            clean_meta['rating'] = float(clean_meta.get('rating', 0.0))
        except (ValueError, TypeError):
            clean_meta['rating'] = 0.0                             

        try:
            clean_meta['current_price'] = float(clean_meta.get('current_price', 0.0))
        except (ValueError, TypeError):
            clean_meta['current_price'] = 0.0                             

                                                                                      
        clean_meta['title'] = str(clean_meta.get('title', ''))
        clean_meta['description'] = str(clean_meta.get('description', ''))
        clean_meta['category'] = str(clean_meta.get('category', ''))
        clean_meta['level'] = str(clean_meta.get('level', ''))
        clean_meta['language'] = str(clean_meta.get('language', ''))
        clean_meta['requirements'] = str(clean_meta.get('requirements', ''))
        clean_meta['what_you_will_learn'] = str(clean_meta.get('what_you_will_learn', ''))                                   

        metas.append(clean_meta)
    
    st.info(f"⏳ Encodage de {len(docs)} documents en embeddings...")
    embeddings = model.encode(docs).tolist()
    st.success(f"✅ {len(embeddings)} embeddings générés.")

    st.info("📥 Ajout des documents à ChromaDB...")
    try:
        collection.add(documents=docs, embeddings=embeddings, ids=ids, metadatas=metas)
        st.success("✅ Documents ajoutés à ChromaDB avec succès.")
    except Exception as e:
        st.error(f"❌ Erreur lors de l'ajout des documents à ChromaDB: {e}")
        st.stop()
        
    return collection

                                               
def set_background_image(image_url):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url({image_url});
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

                                                        

def main():
    st.set_page_config(page_title="🤖 Chatbot IA", layout="wide")

                                 
                                                                                                
                                                                             
    

    st.title("🤖 Chatbot IA: Recherche de Cours / Certificats")

                                                          
    data = load_json()
    collection = initialize_chroma(data)

                                                     
    st.header("🔎 Effectuer une Recherche")

    choice = st.selectbox("Que voulez-vous chercher ?", ["Cours", "Certificat"])
    question = st.text_input("Entrez votre question ou besoin (ex: 'cours sur Python pour débutants', 'certificat en cybersécurité'):")

                                                                                           
                                                                    
    filtered_data_by_choice = [d for d in data if str(d.get("category")).lower() == (("courses" if choice == "Cours" else "certificats").lower())]

    selected_level = None
    min_price = 0.0
    max_price = 500.0

    if choice == "Cours":
                                                                                        
        all_levels = set()
        for d in filtered_data_by_choice:
            level = d.get("level")
            if level is not None:
                if isinstance(level, list):
                    all_levels.update(map(str, level))                                    
                else:
                    all_levels.add(str(level))                                         
        
        levels = sorted(list(all_levels))
        
        if "Inconnu" not in levels:                                             
            levels.insert(0, "Tous les niveaux")                                        
        else:
             levels.remove("Inconnu")                                                                 
             levels.insert(0, "Tous les niveaux")
             levels.insert(1, "Inconnu")


        selected_level = st.selectbox("Choisissez un niveau :", levels, index=0)                                    

        col_min_price, col_max_price = st.columns(2)
        with col_min_price:
            min_price = st.number_input("Prix minimum (€)", min_value=0.0, value=0.0, step=10.0)
        with col_max_price:
            max_price = st.number_input("Prix maximum (€)", min_value=0.0, value=500.0, step=10.0)

        if min_price > max_price:
            st.error("❌ Le prix minimum ne peut pas être supérieur au prix maximum.")
            return

    if st.button("Lancer la recherche"):
        if not question:
            st.warning("⚠️ Veuillez formuler une question pour lancer la recherche.")
            return

        st.info("🔍 Lancement de la recherche...")
        
                                  
        question_emb = load_model().encode([question]).tolist()

                                                                                                    
                                                                                        
        try:
            results = collection.query(query_embeddings=question_emb, n_results=50)                                  
        except Exception as e:
            st.error(f"❌ Erreur lors de la recherche dans ChromaDB: {e}")
            return

        found_items = []
        if results and results['documents'] and results['metadatas']:
            for doc_text, meta in zip(results['documents'][0], results['metadatas'][0]):
                                                                              
                                                                                    
                meta_category = str(meta.get('category', '')).lower()
                expected_category = ("courses" if choice == "Cours" else "certificats").lower()

                if meta_category != expected_category:
                    continue                                                                      

                if choice == "Cours":
                                         
                    meta_level = str(meta.get('level', '')).lower()
                    if selected_level != "Tous les niveaux":
                                                                                                
                        if selected_level.lower() != meta_level:
                            continue

                                       
                    try:
                        price = float(meta.get('current_price', 0.0))
                    except (ValueError, TypeError):
                        price = 0.0                                                          

                    if not (min_price <= price <= max_price):
                        continue
                
                                                                           
                found_items.append(meta)
        
                                                                                 
        found_items = found_items[:10]

        if found_items:
            st.success(f"✅ {len(found_items)} résultats pertinents trouvés avec vos critères :")
            for item in found_items:
                st.subheader(item.get('title', 'Titre Inconnu'))
                st.write(f"**Catégorie :** {item.get('category', 'Non renseignée')}")
                st.write(item.get('description', 'Pas de description disponible.'))
                if 'what_you_will_learn' in item and item['what_you_will_learn']:
                    st.write("**Ce que vous apprendrez :**")
                    st.markdown(f"*{item['what_you_will_learn']}*")                                   
                
                                                                             
                if choice == "Cours":
                    st.write(f"**Niveau :** {item.get('level', 'Non renseigné')}")
                    st.write(f"**Prix :** {item.get('current_price', 'Non renseigné')} €")
                
                st.divider()
        else:
            st.error("❌ Aucun résultat trouvé avec vos critères de recherche.")

                                         
if __name__ == "__main__":
    main()