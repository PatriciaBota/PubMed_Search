from Bio import Entrez
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from collections import Counter
import time
from http.client import IncompleteRead

# Example list of journals with IF > 2 in cardiology and AI
journals_with_high_if = [
    "Journal of the American College of Cardiology",
    "Circulation",
    "Nature Reviews Cardiology",
    "JAMA Cardiology",
    "European Journal of Heart Failure",
    "JACC. Heart Failure",
    "Circulation Research",
    "JACC. Cardiovascular imaging",
    "European heart journal",
    "Nature Cardiovascular Research",
    "Circulation. Heart Failure",
    "Circulation. Arrhythmia and Electrophysiology",
    "JACC. Clinical Electrophysiology",
    "European Heart Journal Cardiovascular Imaging",
    "Europace",
    "JACC. Cardiovascular Interventions",
    "JACC. CardioOncology",
    "Cardiovascular Research",
    "JACC. Basic to Translational Science",
    "Circulation. Genomic and Precision Medicine",
    "Cardiovascular Diabetology",
    "Arteriosclerosis, Thrombosis, and Vascular Biology",
    "Circulation. Cardiovascular Quality and Outcomes",
    "Journal of Heart and Lung Transplantation",
    "Stroke",
    "Resuscitation",
    "EuroIntervention",
    "Basic Research in Cardiology",
    "Circulation. Cardiovascular Interventions",
    "Journal of Cardiovascular Magnetic Resonance",
    "European Heart Journal Quality of Care & Clinical Outcomes",
    "European Stroke Journal",
    "Journal of the American Heart Association",
    "Chest",
    "American Heart Journal",
    "Heart Rhythm",
    "Journal of the American Society of Echocardiography",
    # AI Journals
    "Science Robotics",
    "International Journal of Computer Vision",
    "Science Robotics",
    "IEEE Transactions on Pattern Analysis and Machine Intelligence",
    "Nature Machine Intelligence",
    "International Journal of Information Management",
    "IEEE/CAA Journal of Automatica Sinica",
    "Annual Review of Control, Robotics, and Autonomous Systems",
    "Computational Visual Media",
    "International Journal of Robotics Research",
    "IEEE Transactions on Fuzzy Systems",
    "IEEE Transactions on Neural Networks and Learning Systems",
    "Transactions of the Association for Computational Linguistics",
    "IEEE Transactions on Cognitive Communications and Networking",
    "Artificial Intelligence Review",
    "Computers and Education. Artificial Intelligence",
    "Journal of the ACM",
    "Journal of Machine Learning Research",
    "Pattern Recognition",
    "Neural Networks",
    "Radiology. Artificial Intelligence",
    "Journal of Metaverse",
    "IEEE Transactions on Intelligent Vehicles",
    "Soft Robotics",
    "Information Sciences",
    "Knowledge-Based Systems",
    "IEEE Intelligent Systems",
    "Energy and AI",
    "International Journal of Information Management Data Insights",
    "IEEE Robotics and Automation Letters",
    "IEEE Computational Intelligence Magazine",
    "Journal of Intelligent Manufacturing",
    "Artificial Intelligence",
    #"Sensors (Basel, Switzerland)",
    #"Scientific reports",
    "Medical image analysis",
    #"Computers in biology and medicine",
    "IEEE transactions on medical imaging",
    #"Medical physics",
    #"Computer methods and programs in biomedicine",
    #"Computerized medical imaging and graphics: the official journal of the Computerized Medical Imaging Society",
    #"Journal of cardiovascular magnetic resonance: official journal of the Society for Cardiovascular Magnetic Resonance",
]


# Set your email
Entrez.email = "your_email@example.com"

def search_pubmed(query, retmax=100):
    handle = Entrez.esearch(db="pubmed", term=query, retmax=retmax, sort="relevance", datetype="pdat", mindate="2021/01/01")
    record = Entrez.read(handle)
    handle.close()
    return record["IdList"]

def fetch_details(id_list, retries=3, delay=5):
    ids = ",".join(id_list)
    for attempt in range(retries):
        try:
            handle = Entrez.efetch(db="pubmed", id=ids, retmode="xml")
            records = Entrez.read(handle)
            handle.close()
            return records
        except (IncompleteRead, Exception) as e:
            print(f"Error fetching details: {e}")
            if attempt < retries - 1:
                print(f"Retrying... ({attempt + 1}/{retries})")
                #time.sleep(delay)
            else:
                print("Max retries reached. Exiting.")
                raise

def extract_article_data(articles):
    article_data = []
    for article in articles['PubmedArticle']:
        medline = article['MedlineCitation']
        pub_date = medline['Article']['Journal']['JournalIssue']['PubDate']
        year = pub_date.get('Year', pub_date.get('MedlineDate', '2021')).split()[0]
        if int(year) >= 2021:
            # Extract DOI if available
            doi = None
            for id in medline['Article']['ELocationID']:
                if id.attributes.get('EIdType') == 'doi':
                    doi = str(id)
                    break
            article_info = {
                'Title': medline['Article']['ArticleTitle'],
                'Journal': medline['Article']['Journal']['Title'],
                'PublicationDate': year,
                'Abstract': medline['Article'].get('Abstract', {}).get('AbstractText', [''])[0],
                'DOI': doi
            }
            article_data.append(article_info)
    return article_data

# Combined search query
combined_query = '''
((machine learning OR deep learning OR artificial intelligence OR classification OR prediction OR assessment OR diagnosis OR prognosis OR detection OR segmentation OR monitoring OR estimation) AND (cardiac OR heart OR cardiovascular))
NOT (review[pt] OR "review"[Publication Type] OR "survey"[ti])
'''


# Perform the search
id_list = search_pubmed(combined_query, retmax=1000)  # Adjust retmax as needed
all_articles = []
if id_list:
    try:
        articles = fetch_details(id_list)
        article_data = extract_article_data(articles)
        all_articles.extend(article_data)
    except Exception as e:
        print(f"Failed to fetch articles for query '{combined_query}': {e}")
print("Total articles found:", len(all_articles))
# Create a DataFrame
df = pd.DataFrame(all_articles)
df['DOI'] = df['DOI'].fillna('')
df['Journal'] = df['Journal'].fillna('')

# Remove duplicates based on the 'Title' column and 'DOI'
df = df.drop_duplicates(subset=['Title'])
df = df.drop_duplicates(subset=['DOI'])
print("Unique articles found:", len(df))

df['Journal_lower'] = df['Journal'].str.lower()

# Convert the list of high impact factor journals to lowercase
journals_with_high_if_lower = [journal.lower() for journal in journals_with_high_if]

# Filter the DataFrame using the lowercase journal names
df_filtered = df[df['Journal_lower'].isin(journals_with_high_if_lower)]

# Drop the temporary 'Journal_lower' column
df = df_filtered.drop(columns=['Journal_lower'])
print("Articles from high-impact journals:", len(df))

# Optionally save to CSV
df.to_csv('pubmed_articles_filtered.csv', index=False)

# Plotting statistics
# 1. Year of Publication
years = df['PublicationDate'].tolist()
year_counts = Counter(years)
years, counts = zip(*sorted(year_counts.items()))

plt.figure(figsize=(10, 5))
plt.bar(years, counts, color='skyblue')
plt.xlabel('Year of Publication')
plt.ylabel('Number of Articles')
plt.title('Number of Articles Published Per Year')
plt.savefig('pubmed_articles_per_year.png', bbox_inches='tight')

# 2. Journal Distribution
journal_counts = Counter(df['Journal'].tolist())
sorted_journal_counts = journal_counts.most_common()
journals, counts = zip(*sorted_journal_counts)

# Set figure size and font size for better readability
plt.figure(figsize=(15, len(journals) // 2))
plt.barh(journals, counts, color='skyblue')
plt.xlabel('Number of Articles')
plt.ylabel('Journal')
plt.title('Journals by Number of Articles')
plt.gca().invert_yaxis()  # Invert y-axis to have the highest at the top

# Adjust font size
plt.xticks(fontsize=8)
plt.yticks(fontsize=8)

# Save and show the plot
plt.tight_layout()
plt.savefig('all_journals_sorted.png', bbox_inches='tight')
plt.close("all")