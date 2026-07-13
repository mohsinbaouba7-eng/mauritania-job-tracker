import re
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

def parse_salary_details(text_content):
    """
    Parses raw job text to extract numeric salary amounts and identify rate types.
    Defaults to 0 and 'Not Specified' if no match is found.
    """
    if not text_content or not isinstance(text_content, str):
        return 0, "Not Specified"
        
    text_lower = text_content.lower()
    salary_numbers = re.findall(r'\b\d+[\s,.]?\d*\b', text_lower)
    
    salary_type = "Not Specified"
    if any(k in text_lower for k in ["hour", "hourly", "heure", "par heure", "/hr", "/h"]):
        salary_type = "Hourly"
    elif any(k in text_lower for k in ["month", "monthly", "mois", "par mois", "/mensuel", "/m"]):
        salary_type = "Monthly"
        
    extracted_amount = 0
    if any(k in text_lower for k in ["mru", "um", "salary", "salaire", "ouguiya"]):
        clean_nums = [int(re.sub(r'[\s,.]', '', n)) for n in salary_numbers if n.strip().isdigit()]
        valid_nums = [n for n in clean_nums if n > 100]
        if valid_nums:
            extracted_amount = max(valid_nums)
            if salary_type == "Not Specified":
                salary_type = "Monthly"

    return extracted_amount, salary_type


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
                    
                    # This extracts all text inside this job card to look for salary details
                    row_text = row.get_text()
                    salary_amount, salary_type = parse_salary_details(row_text)
                    
                    scraped_jobs.append({
                        "Job Title": title,
                        "Company": company,
                        "Category": bucket_name,
                        "Source": "Techghil",
                        "Job Count": 1,
                        "Salary Amount": salary_amount,
                        "Salary Type": salary_type
                    })


            # --- PLATFORM B: BETA CONSEILS ---
            beta_soup = scrape_board(
                url="https://www.beta.mr/beta/liste_offres/11",
                params={"search": term},
                headers=headers, platform_name="Beta Conseils"
            )
            if beta_soup:
                for row in beta_soup.find_all('div', class_='offre-box'):
                    # Keep whatever title/company extraction code you already have here for Beta Conseils, then add:
                    title = row.find('h3').text.strip() if row.find('h3') else term # (or whatever tag Beta uses)
                    
                    # Extract text from the Beta Conseils row
                    row_text = row.get_text()
                    salary_amount, salary_type = parse_salary_details(row_text)
                    
                    scraped_jobs.append({
                        "Job Title": title,
                        "Company": "N/A", # Change this to your Beta Conseils company logic
                        "Category": bucket_name,
                        "Source": "Beta Conseils",
                        "Job Count": 1,
                        "Salary Amount": salary_amount,
                        "Salary Type": salary_type
                    })

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
                    
                    # Extract raw text from the Novojob card to scan for salary details
                    card_text = card.get_text()
                    salary_amount, salary_type = parse_salary_details(card_text)
                    
                    scraped_jobs.append({
                        "Job Title": title,
                        "Company": company,
                        "Category": bucket_name,
                        "Source Platform": "Novojob",
                        "Job Count": 1,
                        "Salary Amount": salary_amount,
                        "Salary Type": salary_type
                    })

            # --- PLATFORM D: EMPLOI MAURITANIE ---
            emploi_soup = scrape_board(
                url="https://maurijob.com/search", 
                params={"query": term},
                headers=headers, platform_name="Emploi Mauritanie"
            )
            if emploi_soup:
                for item in emploi_soup.find_all('div', class_='job-post'):
                    title = item.find('a', class_='job-title').text.strip() if item.find('a', class_='job-title') else term
                    company = item.find('div', class_='job-comp').text.strip() if item.find('div', class_='job-comp') else "N/A"
                    
                    # Extract text from the Emploi Mauritanie item element
                    item_text = item.get_text()
                    salary_amount, salary_type = parse_salary_details(item_text)
                    
                    scraped_jobs.append({
                        "Job Title": title,
                        "Company": company,
                        "Category": bucket_name,
                        "Source Platform": "Emploi Mauritanie",
                        "Job Count": 1,
                        "Salary Amount": salary_amount,
                        "Salary Type": salary_type
                    })

            linkedin_soup = scrape_board(
                url="https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search", 
                params={"keywords": term, "location": "Worldwide"},
                headers=headers, platform_name="LinkedIn"
            )
            if linkedin_soup:
                for post in linkedin_soup.find_all('div', class_='base-card'):
                    title = post.find('h3', class_='base-search-card__title').text.strip() if post.find('h3', class_='base-search-card__title') else term
                    company = post.find('h4', class_='base-search-card__subtitle').text.strip() if post.find('h4', class_='base-search-card__subtitle') else "N/A"
                    
                    # Extract text from the LinkedIn post element
                    post_text = post.get_text()
                    salary_amount, salary_type = parse_salary_details(post_text)
                    
                    scraped_jobs.append({
                        "Job Title": title,
                        "Company": company,
                        "Category": bucket_name,
                        "Source Platform": "LinkedIn",
                        "Job Count": 1,
                        "Salary Amount": salary_amount,
                        "Salary Type": salary_type
                    })

# --- PLATFORM F: RIMTIC (MAURITANIA) ---
        rimtic_soup = scrape_board(
            url="https://rimtic.com/fr/offre-emploi",
            params={"search": term},
            headers=headers,
            platform_name="Rimtic"
        )
        
        if rimtic_soup:
            for post in rimtic_soup.find_all(['li', 'div', 'a'], class_=lambda c: c and 'offre' in c.lower()):
                title_element = post.find(['h3', 'h4', 'span']) or post
                title = title_element.text.strip() if title_element else "N/A"
                
                if title != "N/A" and len(title) > 3:
                    post_text = post.get_text()
                    salary_amount, salary_type = parse_salary_details(post_text)
                    
                    scraped_jobs.append({
                        "Job Title": title,
                        "Company": "Rimtic Client",
                        "Category": bucket_name,
                        "Source Platform": "Rimtic",
                        "Job Count": 1,
                        "Salary Amount": salary_amount,
                        "Salary Type": salary_type
                    })

        # --- PLATFORM G: ARBEITNOW (WORLDWIDE PUBLIC API) ---
        try:
            global_api_url = f"https://www.arbeitnow.com/api/job-board-api?search={term}"
            api_response = requests.get(global_api_url, headers=headers, timeout=10)
            
            if api_response.status_code == 200:
                api_data = api_response.json()
                for job_entry in api_data.get('data', [])[:5]:
                    api_text_blob = f"{job_entry.get('title', '')} {job_entry.get('description', '')}"
                    salary_amount, salary_type = parse_salary_details(api_text_blob)
                    
                    scraped_jobs.append({
                        "Job Title": job_entry.get('title'),
                        "Company": job_entry.get('company_name'),
                        "Category": bucket_name,
                        "Source Platform": "Arbeitnow Worldwide",
                        "Job Count": 1,
                        "Salary Amount": salary_amount,
                        "Salary Type": salary_type
                    })
        except Exception as e:
            print(f"[-] Global API match skipped for term '{term}': {e}")


  # --- PLATFORM H: INDEED ---
            try:
                indeed_url = f"https://www.indeed.com/jobs?q={term.replace(' ', '+')}&l=Mauritania"
                indeed_response = requests.get(indeed_url, headers=headers, timeout=10)
                
                if indeed_response.status_code == 200:
                    indeed_soup = BeautifulSoup(indeed_response.text, 'html.parser')
                    job_cards = indeed_soup.find_all('div', class_='job_seen_beacon')
                    
                    for card in job_cards[:5]:
                        title_element = card.find('h2', class_='jobTitle')
                        job_title = title_element.get_text(strip=True) if title_element else term
                        
                        if job_title.lower().startswith("new"):
                            job_title = job_title[3:].strip()
                        
                        company_element = card.find('span', class_='companyName') or card.find('span', {'data-testid': 'company-name'})
                        company_name = company_element.get_text(strip=True) if company_element else "N/A"
                        
                        salary_element = card.find('div', class_='metadata salary-snippet-container')
                        salary_amount = 0
                        salary_type = "Yearly"
                        
                        if salary_element:
                            raw_salary_text = salary_element.get_text(strip=True)
                            digits = [s for s in raw_salary_text.split() if any(char.isdigit() for char in s)]
                            if digits:
                                try:
                                    clean_num = ''.join(c for c in digits[0] if c.isdigit())
                                    salary_amount = int(clean_num)
                                except ValueError:
                                    salary_amount = 0

                        scraped_jobs.append({
                            "Job Title": job_title,
                            "Company": company_name,
                            "Category": bucket_name,
                            "Source Platform": "Indeed",
                            "Job Count": 1,
                            "Salary Amount": salary_amount,
                            "Salary Type": salary_type
                        })
            except Exception as e:
                print(f"[-] Indeed match skipped for term '{term}': {e}")

            
        time.sleep(1)

    # Process and group data by Category AND Source platform
    df = pd.DataFrame(scraped_jobs)
        
    if not df.empty:
            df = df.drop_duplicates(subset=['Job Title', 'Company'])
            counts = df.groupby(['Category', 'Source Platform']).size().reset_index(name='Job Count')
            counts.columns = ['Job Category', 'Source Platform', 'Job Count']
            
            df.to_csv('mauritania_all_data_jobs.csv', index=False)
            print("[+] Local testing complete. Dataset saved to 'mauritania_all_data_jobs.csv'.")
    else:
            pd.DataFrame(columns=['Job Category', 'Source Platform', 'Job Count']).to_csv('mauritania_all_data_jobs.csv', index=False)
            print("[-] Complete. No active matching positions found today.")

if __name__ == "__main__":
    main_pipeline()

            