import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import tldextract
import time
import os
import warnings

# ---------------- CONFIG ----------------
BASE_DIR = r"D:\final year project please"
OUTPUT_DIR = os.path.join(BASE_DIR, "Project_folder")

INPUT_FILE = os.path.join(BASE_DIR, "Balanced_dataset.csv")
OUTPUT_DATASET = os.path.join(OUTPUT_DIR, "Feature_dataset_3000_part2.csv")
FAILED_LOG = os.path.join(OUTPUT_DIR, "Skipped_URLs_3000_part2.csv")

TIMEOUT = 12
RETRIES = 2
SLEEP_TIME = 0.3

START_INDEX = 3000   # skip first 3000 URLs (CSV rows 2–3001)
BATCH_SIZE = 3000

# suppress SSL warnings (intentional verify=False)
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# ---------------- FEATURE EXTRACTION ----------------
def extract_features(url):
    for attempt in range(RETRIES + 1):
        try:
            response = requests.get(
                url,
                timeout=TIMEOUT,
                headers={"User-Agent": "Mozilla/5.0"},
                allow_redirects=True,
                verify=False
            )

            html = response.text if response.text else ""
            soup = BeautifulSoup(html, "html.parser")
            base_domain = tldextract.extract(url).domain

            # -------- HTML FEATURES --------
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

            num_hidden_inputs = len(soup.find_all("input", {"type": "hidden"}))
            num_password_inputs = len(soup.find_all("input", {"type": "password"}))

            external_form_action = 0
            for form in soup.find_all("form", action=True):
                action_domain = tldextract.extract(form["action"]).domain
                if action_domain and action_domain != base_domain:
                    external_form_action = 1
                    break

            # -------- JAVASCRIPT FEATURES --------
            scripts_text = " ".join(
                script.get_text().lower() for script in soup.find_all("script")
            )

            right_click_disabled = 1 if "contextmenu" in scripts_text else 0
            popup_window = 1 if "window.open" in scripts_text else 0
            eval_js_count = scripts_text.count("eval(")

            features = {
                "num_script": num_script,
                "num_form": num_form,
                "num_iframe": num_iframe,
                "num_links": num_links,
                "num_external_links": external_links,
                "num_hidden_inputs": num_hidden_inputs,
                "num_password_inputs": num_password_inputs,
                "external_form_action": external_form_action,
                "right_click_disabled": right_click_disabled,
                "popup_window": popup_window,
                "eval_js_count": eval_js_count,
                "url_length": len(url),
                "has_https": 1 if url.startswith("https") else 0,
                "page_accessible": 1
            }

            return features, None

        except Exception as e:
            if attempt == RETRIES:
                return {
                    "num_script": -1,
                    "num_form": -1,
                    "num_iframe": -1,
                    "num_links": -1,
                    "num_external_links": -1,
                    "num_hidden_inputs": -1,
                    "num_password_inputs": -1,
                    "external_form_action": -1,
                    "right_click_disabled": -1,
                    "popup_window": -1,
                    "eval_js_count": -1,
                    "url_length": len(url),
                    "has_https": 1 if url.startswith("https") else 0,
                    "page_accessible": 0
                }, str(e)

# ---------------- MAIN ----------------
os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv(INPUT_FILE)

# 🔹 Select NEXT 3000 URLs
df = df.iloc[START_INDEX : START_INDEX + BATCH_SIZE]
TOTAL_ROWS = len(df)

print(f"Starting crawling for rows {START_INDEX + 1} to {START_INDEX + TOTAL_ROWS}...\n")

final_data = []
failed_urls = []

for i, row in df.iterrows():
    url = row["url"]
    label = row["label"]

    feats, error = extract_features(url)

    final_data.append({
        "url": url,
        "label": label,
        **feats
    })

    if error:
        failed_urls.append({
            "url": url,
            "label": label,
            "reason": error
        })
        print(f"[ACCESS ISSUE] {url} | label={label}")

    time.sleep(SLEEP_TIME)
    print(f"Processed index {i + 1}")

# ---------------- SAVE FILES ----------------
final_df = pd.DataFrame(final_data)
failed_df = pd.DataFrame(failed_urls)

final_df.to_csv(OUTPUT_DATASET, index=False)

if not failed_df.empty:
    failed_df.to_csv(FAILED_LOG, index=False)

print("\nCrawling finished")
print("Rows processed:", len(final_df))
print("Access issues:", len(failed_df))
