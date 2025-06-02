import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, WebDriverException, ElementClickInterceptedException, StaleElementReferenceException
)
from bs4 import BeautifulSoup
import json
import time
import re
import html
import os

def scrape_udemy_chatgpt_courses():
    # URL pour la catégorie "ChatGPT"
    BASE_SEARCH_URL = "https://www.udemy.com/topic/microsoft-ai-102/"
    
    
    NUM_PAGES_TO_SCRAPE = 5

    options = uc.ChromeOptions()
    
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-extensions')
    options.add_argument('--log-level=3')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

    driver = None
    all_courses_data = []

    
    chromedriver_path = "./chromedriver"
    

    absolute_chromedriver_path = os.path.abspath(chromedriver_path)

    print(f"DEBUG: Le script s'attend à trouver 'chromedriver' à l'emplacement relatif : {chromedriver_path}")
    print(f"DEBUG: Chemin absolu calculé pour 'chromedriver' : {absolute_chromedriver_path}")

    if not os.path.exists(absolute_chromedriver_path):
        print(f"ERREUR CRITIQUE DE FICHIER: Le fichier '{absolute_chromedriver_path}' N'EXISTE PAS.")
        print("Veuillez vous assurer que 'chromedriver' est décompressé, exécutable, et placé dans le même dossier que le script.")
        print(f"Le dossier actuel du script est : {os.getcwd()}")
        return
    else:
        print(f"DEBUG: Le fichier '{absolute_chromedriver_path}' EXISTE.")
        if not os.access(absolute_chromedriver_path, os.X_OK):
            print(f"ERREUR CRITIQUE DE PERMISSION: Le fichier '{absolute_chromedriver_path}' N'EST PAS EXÉCUTABLE.")
            print("Veuillez exécuter 'chmod +x chromedriver' dans votre terminal, dans le dossier où se trouve chromedriver.")
            return
        else:
            print(f"DEBUG: Le fichier '{absolute_chromedriver_path}' EST EXÉCUTABLE.")

    try:
        print("1. Lancement du navigateur Chrome avec undetected_chromedriver...")
        driver = uc.Chrome(options=options, driver_executable_path=chromedriver_path)
        print("Navigateur lancé avec succès.")

        course_urls_to_visit = []
        for page_num in range(1, NUM_PAGES_TO_SCRAPE + 1):
            # L'URL de base pour la première page, avec paramètre p pour les pages suivantes
            current_page_url = BASE_SEARCH_URL if page_num == 1 else f"{BASE_SEARCH_URL}?p={page_num}"

            print(f"\n--- Scraping de la page de résultats {page_num}/{NUM_PAGES_TO_SCRAPE} ---")
            print(f"2. Navigation vers: {current_page_url}")
            driver.get(current_page_url)
            print("URL demandée. Attente du chargement des cartes de cours (environ 25 seconds).")
            time.sleep(25) # Donnez un peu plus de temps pour le chargement initial

            # --- Section pour gérer le pop-up "Ouvrir une application externe" ---
            try:
                print("   -> Tentative de gérer le pop-up 'Ouvrir une application externe'...")
                cancel_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='Annuler'] | //button[text()='Cancel']"))
                )
                cancel_button.click()
                print("   -> Pop-up fermé en cliquant sur 'Annuler'.")
            except TimeoutException:
                print("   -> Pas de pop-up 'Ouvrir une application externe' détecté ou géré dans le délai.")
            except Exception as e:
                print(f"   -> Erreur lors de la gestion du pop-up : {e}")
            # --- Fin de la section pop-up ---


            print(f"3. URL actuellement affichée dans le navigateur: {driver.current_url}")

            try:
                print("   -> Attente de la présence des cartes de cours sur la page avec le nouveau sélecteur...")
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-purpose='container']"))
                )
                print("   -> Cartes de cours détectées avec le nouveau sélecteur.")

                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')

                course_cards = soup.find_all('div', {'data-purpose': 'container'})

                if not course_cards:
                    print(f"Aucune carte de cours trouvée sur la page {page_num} avec le nouveau sélecteur. Cela peut indiquer la fin des résultats ou un problème de chargement.")
                    break

                print(f"Trouvé {len(course_cards)} cours sur la page de résultats {page_num}.")

                for i, card_soup in enumerate(course_cards):
                    course_temp_info = {}

                    title_link_element = card_soup.select_one('h3[data-purpose="course-title-url"] a')

                    if title_link_element:
                        # Créer une copie de l'élément pour supprimer le div SEO caché avant d'extraire le texte
                        title_soup_copy = BeautifulSoup(str(title_link_element), 'html.parser')
                        hidden_seo_div = title_soup_copy.find('div', class_='ud-sr-only')
                        if hidden_seo_div:
                            hidden_seo_div.decompose() # Supprimer le div caché

                        course_temp_info['title'] = title_soup_copy.get_text(strip=True)
                        # S'assurer que l'URL est absolue
                        course_temp_info['url'] = "https://www.udemy.com" + title_link_element['href'] if title_link_element.get('href') and title_link_element['href'].startswith('/') else title_link_element['href']
                    else:
                        course_temp_info['title'] = None
                        course_temp_info['url'] = None

                    if course_temp_info['url']:
                        course_urls_to_visit.append(course_temp_info)
                    else:
                        print(f"  - URL du cours non trouvée pour : {course_temp_info.get('title', 'N/A')}. Skip.")

                # --- PARTIE POUR GÉRER LA PAGINATION (PASSER À LA PAGE SUIVANTE) ---
                if page_num < NUM_PAGES_TO_SCRAPE: # Si ce n'est pas la dernière page que nous voulons scraper
                    # Sélecteurs potentiels pour le bouton "page suivante"
                    next_button_selectors = [
                        "a[aria-label='next page']",
                        "a[data-page='+1']",
                        "a[rel='next']",
                        "a[aria-label='Next page']", "button[aria-label='Next page']",
                        "a[aria-label='Page suivante']", "button[aria-label='Page suivante']", # Localisation française
                        "a[data-purpose='pagination-button-next']", "button[data-purpose='pagination-button-next']",
                        "a.pagination_next__aBqfT", # Classe spécifique si présente
                        "a:has(svg use[xlink:href='#icon-next'])", "button:has(svg use[xlink:href='#icon-next'])"
                    ]
                    
                    next_button_found = False
                    for selector in next_button_selectors:
                        try:
                            print(f"   -> Tentative de trouver le bouton 'page suivante' avec le sélecteur : '{selector}'")
                            next_button = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                            # Faire défiler et cliquer en utilisant JavaScript pour plus de robustesse
                            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                            time.sleep(1) # Petit délai après le scroll
                            next_button.click()
                            print(f"   -> Bouton 'page suivante' cliqué avec succès via le sélecteur '{selector}'. Attente du chargement de la nouvelle page.")
                            time.sleep(5) # Laisser le temps à la nouvelle page de se charger
                            next_button_found = True
                            break # Sortir de la boucle si le bouton est trouvé et cliqué
                        except (TimeoutException, ElementClickInterceptedException, StaleElementReferenceException):
                            # Essayer le sélecteur suivant si l'actuel échoue
                            continue 
                        except Exception as e:
                            print(f"   -> Erreur inattendue avec le sélecteur '{selector}': {e}")
                            continue

                    if not next_button_found:
                        print(f"   -> Aucun bouton 'page suivante' trouvé ou cliquable pour passer à la page {page_num + 1} après toutes les tentatives. Fin de la pagination.")
                        break # Arrêter si aucun bouton suivant n'est trouvé
                else:
                    print(f"   -> Nombre maximum de pages ({NUM_PAGES_TO_SCRAPE}) à scraper atteint. Arrêt de la pagination.")

            except TimeoutException:
                print(f"4. Pas de cartes de cours trouvées sur la page {page_num} dans le délai imparti. Arrêt du scraping des pages de résultats.")
                break
            except Exception as e:
                print(f"5. Une erreur inattendue s'est produite pendant le processus de la page {page_num}: {e}. Arrêt du scraping des pages de résultats.")
                break

        print(f"\nDébut du scraping des pages de détails pour {len(course_urls_to_visit)} cours pour l'extraction du nombre d'étudiants, des objectifs, de la description, du prix, des exigences, de la langue et du rating.")
        for i, course_info in enumerate(course_urls_to_visit):
            course_url = course_info['url']
            print(f"\n--- Visiting Course {i+1}/{len(course_urls_to_visit)}: {course_info.get('title', 'N/A')} ---")
            print(f"  -> Navigating to: {course_url}")

            # Initialiser les variables pour les informations détaillées
            students_enrolled = None
            what_you_will_learn = []
            description_text = None
            current_price = None
            original_price = None
            discount_percentage = None
            requirements = []
            course_language = None
            rating = None

            try:
                driver.get(course_url)
                print("  -> URL demandée. Attente du chargement de l'élément d'inscription et autres sections.")
                # Attendre qu'un élément clé de la page de détails soit présent
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-purpose='enrollment']"))
                )
                time.sleep(5) # Un petit délai supplémentaire après l'attente explicite pour tout contenu dynamique

                detail_soup = BeautifulSoup(driver.page_source, 'html.parser')

                # --- Extraction du nombre d'étudiants inscrits ---
                # The provided outerHTML for rating also contains the enrollment div
                enrollment_div = detail_soup.find('div', {'data-purpose': 'enrollment'})
                if enrollment_div:
                    enrollment_text = enrollment_div.get_text(strip=True)
                    cleaned_enrollment_text = re.sub(r'[^\d]', '', enrollment_text) # Supprimer les caractères non numériques
                    try:
                        students_enrolled = int(cleaned_enrollment_text)
                        print(f"  -> Nombre d'étudiants trouvé : {students_enrolled}")
                    except ValueError:
                        print(f"  -> Impossible de convertir '{enrollment_text}' en nombre d'étudiants.")
                        students_enrolled = None
                else:
                    print("  -> Div 'data-purpose=\"enrollment\"' non trouvé dans le HTML.")

                # --- Extraction de la langue du cours ---
                language_div = detail_soup.find('div', {'data-purpose': 'lead-course-locale'})
                if language_div:
                    course_language = language_div.get_text(strip=True)
                    # Supprimer "Course Language" si c'est préfixé (peut être ajouté par aria-label)
                    course_language = course_language.replace('Course Language', '').strip() 
                    print(f"  -> Langue du cours trouvée : {course_language}")
                else:
                    print("  -> Langue du cours non trouvée (div 'data-purpose=\"lead-course-locale\"' manquant).")

                # --- Extraction du Rating ---
                rating_span = detail_soup.find('span', {'data-purpose': 'rating-number'})
                if rating_span:
                    rating = rating_span.get_text(strip=True)
                    print(f"  -> Rating trouvé : {rating}")
                else:
                    print("  -> Rating non trouvé (span 'data-purpose=\"rating-number\"' manquant).")


                # --- Extraction de "What you'll learn" ---
                learn_section = detail_soup.find('div', class_='what-you-will-learn--what-will-you-learn--jsm83')
                if learn_section:
                    # CORRECTED LINE: Pass multiple classes as a list to class_
                    objectives_list_ul = learn_section.find('ul', class_=['ud-unstyled-list', 'what-you-will-learn--objectives-list--qsvE2'])
                    if objectives_list_ul:
                        # Itérer sur les li, puis trouver le div contenant le texte de l'objectif
                        for item in objectives_list_ul.find_all('li'): # Find all 'li' elements directly
                            # The text is typically within a div with class 'ud-block-list-item-content'
                            content_div = item.find('div', class_='ud-block-list-item-content')
                            if content_div:
                                what_you_will_learn.append(content_div.get_text(strip=True))
                        print(f"  -> Objectifs d'apprentissage trouvés : {len(what_you_will_learn)} éléments.")
                    else:
                        print("  -> Liste des objectifs (ul.what-you-will-learn--objectives-list) non trouvée.")
                else:
                    print("  -> Section 'What you'll learn' (div.what-you-will-learn--what-will-you-learn) non trouvée.")


                # --- Extraction de la "Description" ---
                description_div = detail_soup.find('div', {'data-purpose': 'course-description'})
                if description_div:
                    description_content_div = description_div.find('div', {'data-purpose': 'safely-set-inner-html:description:description'})
                    if description_content_div:
                        # Extraire tout le texte des balises pertinentes dans la description
                        all_text_elements = description_content_div.find_all(['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div'])
                        description_parts = []
                        for elem in all_text_elements:
                            text = elem.get_text(strip=True)
                            if text:
                                description_parts.append(text)
                        description_text = "\n\n".join(description_parts)
                        
                        # Supprimer la section "Who this course is for:" si elle est involontairement incluse
                        if description_text and "Who this course is for:" in description_text:
                            description_text = description_text.split("Who this course is for:")[0].strip()

                        print(f"  -> Description trouvée (longueur : {len(description_text) if description_text else 0}).")
                    else:
                        print("  -> Contenu de la description non trouvé dans data-purpose='course-description'.")
                else:
                    print("  -> Section 'Description' (div data-purpose='course-description') non trouvée.")


                # --- Extraction des "Requirements" ---
                # Rechercher le h2 avec data-purpose="requirements-title" puis son ul frère
                requirements_section_title = detail_soup.find('h2', {'data-purpose': 'requirements-title'})
                if requirements_section_title:
                    requirements_list_ul = requirements_section_title.find_next_sibling('ul', class_='ud-unstyled-list')
                    if requirements_list_ul:
                        for item in requirements_list_ul.find_all('div', class_='ud-block-list-item-content'):
                            req_text = item.get_text(strip=True)
                            if req_text:
                                requirements.append(req_text)
                        print(f"  -> Exigences trouvées : {len(requirements)} éléments.")
                    else:
                        print("  -> Liste des exigences (ul.ud-unstyled-list) non trouvée après le titre.")
                else:
                    print("  -> Titre de la section 'Requirements' (h2 data-purpose='requirements-title') non trouvé.")


                # --- Extraction du Prix ---
                price_container = detail_soup.find('div', {'data-purpose': 'price-text-container'})
                if price_container:
                    current_price_element = price_container.find('div', {'data-purpose': 'course-price-text'})
                    if current_price_element:
                        current_price = current_price_element.get_text(strip=True)
                        # Nettoyer la chaîne de prix (supprimer les symboles de devise, garder les chiffres et la décimale, convertir la virgule en point)
                        current_price = re.sub(r'[^\d.,]+', '', current_price).replace(',', '.')
                        print(f"  -> Prix actuel trouvé : {current_price}")
                    else:
                        print("  -> Élément de prix actuel non trouvé.")

                    original_price_element = price_container.find('div', {'data-purpose': 'course-old-price-text'})
                    if original_price_element:
                        original_price = original_price_element.get_text(strip=True)
                        original_price = re.sub(r'[^\d.,]+', '', original_price).replace(',', '.')
                        print(f"  -> Prix original trouvé : {original_price}")
                    else:
                        print("  -> Élément de prix original non trouvé.")

                    discount_element = price_container.find('div', {'data-purpose': 'discount-percentage'})
                    if discount_element:
                        discount_percentage = discount_element.get_text(strip=True)
                        print(f"  -> Pourcentage de réduction trouvé : {discount_percentage}")
                    else:
                        print("  -> Élément de pourcentage de réduction non trouvé.")
                else:
                    print("  -> Conteneur de prix non trouvé.")


                # Ajouter toutes les données extraites au dictionnaire course_info
                course_info['students_enrolled'] = students_enrolled
                course_info['what_you_will_learn'] = what_you_will_learn
                course_info['description'] = description_text
                course_info['current_price'] = current_price
                course_info['original_price'] = original_price
                course_info['discount_percentage'] = discount_percentage
                course_info['requirements'] = requirements
                course_info['course_language'] = course_language
                course_info['rating'] = rating

                all_courses_data.append(course_info)

            except TimeoutException:
                print(f"  -> L'un des éléments d'attente n'a pas été trouvé dans le délai imparti pour {course_url}. Le scraping des détails est annulé pour ce cours.")
                # S'assurer que toutes les clés sont présentes même en cas d'erreur pour la cohérence
                course_info.update({
                    'students_enrolled': None,
                    'what_you_will_learn': [],
                    'description': None,
                    'current_price': None,
                    'original_price': None,
                    'discount_percentage': None,
                    'requirements': [],
                    'course_language': None,
                    'rating': None
                })
                all_courses_data.append(course_info)
            except Exception as e:
                print(f"  -> Une erreur s'est produite lors du traitement de la page de détails {course_url} : {e}. Skip ce cours.")
                # S'assurer que toutes les clés sont présentes même en cas d'erreur pour la cohérence
                course_info.update({
                    'students_enrolled': None,
                    'what_you_will_learn': [],
                    'description': None,
                    'current_price': None,
                    'original_price': None,
                    'discount_percentage': None,
                    'requirements': [],
                    'course_language': None,
                    'rating': None
                })
                all_courses_data.append(course_info)

    except WebDriverException as e:
        print(f"\nERREUR CRITIQUE DE SELENIUM/CHROMEDRIVER: {e}")
        print("Le navigateur n'a pas pu être lancé ou géré correctement.")
        print("Veuillez vous assurer que Chrome est installé, et que l'exécutable 'chromedriver'")
        print("correspondant à votre version de Chrome est dans le même répertoire que ce script et est exécutable.")
    except Exception as e:
        print(f"\nUNE ERREUR GÉNÉRALE INATTENDUE S'EST PRODUITE: {e}")
    finally:
        if driver:
            print("\n6. Fermeture du navigateur.")
            driver.quit()

    if all_courses_data:
        json_filename = "udemy-microsoft AI.json" # Changed filename
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(all_courses_data, f, ensure_ascii=False, indent=4)
        print(f"\nScraping terminé. {len(all_courses_data)} cours (titre, URL, nombre d'étudiants, objectifs, description, prix, exigences, langue, rating) sauvegardés dans {json_filename}")
    else:
        print("\nAucun cours n'a pu être scrapé. Veuillez revoir les messages d'erreur ci-dessus.")

if __name__ == "__main__":
    scrape_udemy_chatgpt_courses()