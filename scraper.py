import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}



def scrape_board(url, params, headers, platform_name):
    """Safely handles HTTP requests for each job board to prevent crashes."""
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code == 200:
            return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"[-] Error reaching {platform_name}: {e}")
    return None

def main_pipeline():
    # Bilingual Keyword Matrix for Mauritania
    role_buckets = {
        "Data Scientist": ["Data Scientist", "Scientifique de données", "Machine Learning", "IA Appliquée"],
        "Data Analyst": ["Data Analyst", "Analyste de données", "Statisticien", "Data Analyste"],
        "Data Engineer": ["Data Engineer", "Ingénieur de données", "Data Architecture", "Data Engineering"],
        "BI & Analytics": ["Business Intelligence", "BI Analyst", "Analyste BI"],
        "Administrative Assistant": ["Assistant Administratif", "Assistant Administrative", "Administrative Assistant", "Assistanat"],
        "Secretary": ["Secretary", "Secrétaire", "Secrétariat"],
        "Cashier": ["Cashier", "Caissier", "Caissière", "Conseillers Clientèles - Caissier"]
    }

    scraped_jobs = []

    # Loop Across All Categories and Targeted Platforms
    for bucket_name, terms in role_buckets.items():
        for term in terms:
            print(f"[+] Searching listings for: '{term}'...")
            
            # --- PLATFORM A: TECHGHIL ---
            techghil_soup = scrape_board(
                url="https://techghil.mr/cms/search/offres/ask",
                params={"q": term, "l": "Nouakchott"},
                headers=headers, platform_name="Techghil"
            )
            if techghil_soup:
                for row in techghil_soup.find_all('div', class_='job-item'): 
                    title = row.find('h3').text.strip() if row.find('h3') else term
                    company = row.find('span', class_='company').text.strip() if row.find('span', class_='company') else "N/A"
                    scraped_jobs.append({"Title": title, "Company": company, "Category": bucket_name, "Source": "Techghil"})

            # --- PLATFORM B: BETA CONSEILS ---
            beta_soup = scrape_board(
                url="https://www.beta.mr/beta/liste_offres/11",
                params={"search": term},
                headers=headers, platform_name="Beta Conseils"
            )
            if beta_soup:
                for row in beta_soup.find_all('div', class_='offre-box'):
                    title = row.find('h4').text.strip() if row.find('h4') else term
                    company = "Beta Conseils Client"
                    scraped_jobs.append({"Title": title, "Company": company, "Category": bucket_name, "Source": "Beta Conseils"})

            # --- PLATFORM C: NOVOJOB MAURITANIE ---
            novojob_soup = scrape_board(
                url="https://www.novojob.com/mauritanie/offres-d-emploi",
                params={"keywords": term},
                headers=headers, platform_name="Novojob"
            )
            if novojob_soup:
                for card in novojob_soup.find_all('div', class_='job-description'):
                    title = card.find('h2').text.strip() if card.find('h2') else term
                    company = card.find('div', class_='company-name').text.strip() if card.find('div', class_='company-name') else "N/A"
                    scraped_jobs.append({"Title": title, "Company": company, "Category": bucket_name, "Source": "Novojob"})

            # --- PLATFORM D: EMPLOI MAURITANIE ---
            emploi_soup = scrape_board(
                url="https://maurijob.com/search", 
                params={"query": term},
                headers=headers, platform_name="Emploi Mauritanie"
            )
            if emploi_soup:
                for item in emploi_soup.find_all('div', class_='job-post'):
                    title = item.find('a', class_='job-title').text.strip()
                    company = item.find('div', class_='job-comp').text.strip()
                    scraped_jobs.append({"Title": title, "Company": company, "Category": bucket_name, "Source": "Emploi Mauritanie"})

            # --- PLATFORM E: LINKEDIN ---
            linkedin_soup = scrape_board(
                url="https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search", 
                params={"keywords": term, "location": "Worldwide"},
                headers=headers, platform_name="LinkedIn"
            )
            if linkedin_soup:
                for post in linkedin_soup.find_all('div', class_='base-card'):
                    title = post.find('h3', class_='base-search-card__title').text.strip()
                    company = post.find('h4', class_='base-search-card__subtitle').text.strip()
                    scraped_jobs.append({"Title": title, "Company": company, "Category": bucket_name, "Source": "LinkedIn"})

            time.sleep(1)

    # Process and group data by Category AND Source platform
    df = pd.DataFrame(scraped_jobs)
    if not df.empty:
        df = df.drop_duplicates(subset=['Title', 'Company'])
        counts = df.groupby(['Category', 'Source']).size().reset_index(name='Job Count')
        counts.columns = ['Job Category', 'Source Platform', 'Job Count']
        counts.to_csv('mauritania_all_data_jobs.csv', index=False)
        print(f"[+] Local testing complete. Dataset saved to 'mauritania_all_data_jobs.csv'.")
    else:
        pd.DataFrame(columns=['Job Category', 'Source Platform', 'Job Count']).to_csv('mauritania_all_data_jobs.csv', index=False)
        print("[-] Complete. No active matching positions found today.")

if __name__ == "__main__":
    main_pipeline()


# --- PLATFORM F: RIMTIC (MAURITANIA) ---
    rimtic_soup = scrape_board(
        url="https://rimtic.com/fr/offre-emploi",
        params={"search": term}, 
        headers=headers, 
        platform_name="Rimtic"
    )
    
    if rimtic_soup:
        # Rimtic lists jobs inside an entry-card layout or item blocks
        for post in rimtic_soup.find_all('div', class_='job-item'):  # Replace with specific class if needed
            title_element = post.find('h3') or post.find('a', class_='job-title')
            title = title_element.text.strip() if title_element else "N/A"
            
            # Append directly into your central scraped_jobs listing array
            if title != "N/A":
                scraped_jobs.append({
                    "Title": title, 
                    "Company": "Rimtic Verified", 
                    "Category": bucket_name,
                    "Source Platform": "Rimtic"
                })

# --- PLATFORM G: ARBEITNOW (WORLDWIDE PUBLIC API) ---
    try:
        # Free open platform endpoint requiring no specialized auth keys
        global_api_url = f"https://www.arbeitnow.com/api/job-board-api?search={term}"
        api_response = requests.get(global_api_url, headers=headers, timeout=10)
        
        if api_response.status_code == 200:
            api_data = api_response.json()
            for job_entry in api_data.get('data', [])[:5]:  # Limit to top 5 results per query to save space
                scraped_jobs.append({
                    "Title": job_entry.get('title'),
                    "Company": job_entry.get('company_name'),
                    "Category": bucket_name,
                    "Source Platform": "Arbeitnow (Worldwide)"
                })
    except Exception as e:
        print(f"[-] Global API match skipped for term '{term}': {e}")

        