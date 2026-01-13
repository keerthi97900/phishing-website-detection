import joblib
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import tldextract
import re
import math
import socket
import ssl
from datetime import datetime
import whois
import warnings

warnings.filterwarnings("ignore")

# ---------------- LOAD MODEL ----------------
model = joblib.load("phishing_xgb_Model.pkl")
feature_columns = joblib.load("model_features.pkl")

# ---------------- URL NORMALIZATION ----------------
def normalize_url(url):
    url = url.strip().lower()

    # ensure scheme
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)

    # remove www
    hostname = parsed.hostname.replace("www.", "") if parsed.hostname else ""

    # remove trailing slash
    path = parsed.path.rstrip("/")

    normalized = f"{parsed.scheme}://{hostname}{path}"

    if parsed.query:
        normalized += "?" + parsed.query

    return normalized


# ---------------- URL FEATURE FUNCTIONS ----------------
def having_ip_address(url):
    return 1 if re.search(r"\d+\.\d+\.\d+\.\d+", url) else 0


def url_entropy(url):
    prob = [url.count(c) / len(url) for c in set(url)]
    return -sum(p * math.log2(p) for p in prob)


def url_shortener(url):
    shorteners = ["bit.ly", "goo.gl", "tinyurl", "t.co", "is.gd", "cutt.ly", "kutt.it"]
    return 1 if any(s in url for s in shorteners) else 0


def domain_age(url):
    try:
        domain = tldextract.extract(url).top_domain_under_public_suffix
        w = whois.whois(domain)
        cd = w.creation_date
        if isinstance(cd, list):
            cd = cd[0]
        return (datetime.now() - cd).days if cd else -1
    except:
        return -1


def dns_record_exists(url):
    try:
        domain = tldextract.extract(url).top_domain_under_public_suffix
        socket.gethostbyname(domain)
        return 1
    except:
        return 0


def ssl_certificate_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme != "https":
            return 0

        context = ssl.create_default_context()
        with context.wrap_socket(
            socket.socket(socket.AF_INET),
            server_hostname=parsed.hostname
        ) as s:
            s.settimeout(5)
            s.connect((parsed.hostname, 443))
            s.getpeercert()

        return 1
    except:
        return 0


# ---------------- HTML FEATURE EXTRACTION ----------------
def extract_html_features(url):
    try:
        r = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"},
            verify=False
        )

        soup = BeautifulSoup(r.text, "html.parser")
        base_domain = tldextract.extract(url).domain

        external_links = 0
        for a in soup.find_all("a", href=True):
            parsed = urlparse(a["href"])
            if parsed.netloc:
                if tldextract.extract(parsed.netloc).domain != base_domain:
                    external_links += 1

        scripts_text = " ".join(s.get_text().lower() for s in soup.find_all("script"))

        return {
            "num_script": len(soup.find_all("script")),
            "num_form": len(soup.find_all("form")),
            "num_iframe": len(soup.find_all("iframe")),
            "num_links": len(soup.find_all("a")),
            "num_external_links": external_links,
            "num_hidden_inputs": len(soup.find_all("input", {"type": "hidden"})),
            "num_password_inputs": len(soup.find_all("input", {"type": "password"})),
            "external_form_action": int(any(
                tldextract.extract(f.get("action", "")).domain != base_domain
                for f in soup.find_all("form", action=True)
            )),
            "right_click_disabled": int("contextmenu" in scripts_text),
            "popup_window": int("window.open" in scripts_text),
            "eval_js_count": scripts_text.count("eval("),
            "page_accessible": 1
        }

    except:
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
            "page_accessible": 0
        }


# ---------------- COMBINED FEATURE EXTRACTOR ----------------
def extract_features(url):
    parsed = urlparse(url)

    features = {
        "url_length": len(url),
        "having_ip_address": having_ip_address(url),
        "count_dots": url.count("."),
        "count_hyphen": url.count("-"),
        "count_at_symbol": url.count("@"),
        "count_question_mark": url.count("?"),
        "count_equal": url.count("="),
        "count_http": url.lower().count("http"),
        "count_https": url.lower().count("https"),
        "path_length": len(parsed.path),
        "subdomain_length": len(tldextract.extract(url).subdomain),
        "url_entropy": url_entropy(url),
        "url_shortener": url_shortener(url),
        "domain_age": domain_age(url),
        "dns_record_exists": dns_record_exists(url),
        "ssl_certificate_valid": ssl_certificate_valid(url)
    }

    features.update(extract_html_features(url))
    return features


# ---------------- PREDICTION FUNCTION ----------------
def predict_url(url):
    features = extract_features(url)
    df = pd.DataFrame([features])

    df = df.reindex(columns=feature_columns, fill_value=-1)

    prediction = model.predict(df)[0]
    probability = model.predict_proba(df)[0][1]

    label = "PHISHING " if prediction == 1 else "LEGITIMATE "

    print("\nURL:", url)
    print("Prediction:", label)
    print("Phishing Probability:", round(probability, 4))


# ---------------- TERMINAL INTERFACE ----------------
if __name__ == "__main__":
    print("\n=== PHISHING WEBSITE DETECTION SYSTEM ===")
    print("Enter a website URL (type 'exit' to quit)\n")

    while True:
        user_input = input("Enter website URL: ").strip()

        if user_input.lower() == "exit":
            print("Exiting system...")
            break

        try:
            clean_url = normalize_url(user_input)
            predict_url(clean_url)
        except Exception as e:
            print("Error processing URL:", e)
