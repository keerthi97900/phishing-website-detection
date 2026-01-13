import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import tldextract
import time
import os

# ---------------- CONFIG ----------------
BASE_DIR = r"D:\final year project please"
OUTPUT_DIR = os.path.join(BASE_DIR, "Project_folder")

INPUT_FILE = os.path.join(BASE_DIR, r"C:\Users\SHYAM\Downloads\Balanced_dataset.csv")
OUTPUT_DATASET = os.path.join(OUTPUT_DIR, "Feature_dataset_New.csv")
FAILED_LOG = os.path.join(OUTPUT_DIR, "Skipped_URLs.csv")

TIMEOUT = 5

# ---------------- FEATURE EXTRACTION ----------------
def extract_features(url):
    try:
        response = requests.get(
            url,
            timeout=TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        if response.status_code != 200 or not response.text:
            return None, "Page not accessible"

        soup = BeautifulSoup(response.text, "html.parser")
        base_domain = tldextract.extract(url).domain

        num_script = len(soup.find_all("script"))
        num_form = len(soup.find_all("form"))
        num_iframe = len(soup.find_all("iframe"))
        num_links = len(soup.find_all("a"))

        external_links = 0
        for a in soup.find_all("a", href=True):
            parsed = urlparse(a["href"])
            if parsed.netloc:
                link_domain = tldextract.extract(parsed.netloc).domain
                if link_domain and link_domain != base_domain:
                    external_links += 1

        features = {
            "num_script": num_script,
            "num_form": num_form,
            "num_iframe": num_iframe,
            "num_links": num_links,
            "num_external_links": external_links,
            "url_length": len(url),
            "has_https": 1 if url.startswith("https") else 0
        }

        return features, None

    except Exception as e:
        return None, str(e)


# ---------------- MAIN ----------------
os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv(INPUT_FILE).head(10)

final_data = []
failed_urls = []

print("Starting crawling...")

for idx, row in df.iterrows():
    url = row["url"]
    label = row["label"]

    feats, error = extract_features(url)

    if feats:
        final_data.append({
            "url": url,
            "label": label,
            **feats
        })
    else:
        failed_urls.append({
            "url": url,
            "label": label,
            "reason": error
        })
        print(f"[SKIPPED] {url} | label={label} | reason={error}")

    time.sleep(0.3)
    print(f"Processed {idx + 1}/10 URLs")

# ---------------- SAVE FILES ----------------
final_df = pd.DataFrame(final_data)
failed_df = pd.DataFrame(failed_urls)

final_df.to_csv(OUTPUT_DATASET, index=False)

if not failed_df.empty:
    failed_df.to_csv(FAILED_LOG, index=False)

print("\nCrawling finished")
print("Final dataset size:", len(final_df))

if not failed_df.empty:
    print("Skipped URLs:", len(failed_df))
    print("Skipped URLs saved to:", FAILED_LOG)
