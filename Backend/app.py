import numpy as np
import xgboost as xgb
from flask import Flask, request, jsonify
from flask_cors import CORS
from urllib.parse import urlparse
import math
import re
import tldextract # A library to accurately extract domain info

# Initialize the Flask application
app = Flask(__name__)
CORS(app) # Enable Cross-Origin Resource Sharing

# --- MODEL LOADING ---
# Load your trained XGBoost model from the JSON file.
try:
    model = xgb.Booster()
    model.load_model('xgb_url_model.json')
    print("XGBoost model loaded successfully from 'xgb_url_model.json'.")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

# --- NEW: WHITELIST OF TRUSTED DOMAINS ---
# This helps prevent false positives for major, well-known websites.
WHITELIST = {
    'google.com',
    'wikipedia.org',
    'youtube.com',
    'facebook.com',
    'amazon.com',
    'apple.com',
    'microsoft.com',
    'nytimes.com',
    'github.com'
}


# --- DEFINE FEATURE NAMES ---
# This list MUST match the order of features the model was trained on.
FEATURE_NAMES = [
    'url_length', 'count_dot', 'count_hyphen', 'count_at', 'count_question',
    'count_equal', 'count_percent', 'count_slash', 'https', 'entropy',
    'domain_length', 'subdomain_length', 'tld_length', 'has_suspicious_word',
    'has_ip'
]

# --- FEATURE EXTRACTION ---
# This function is now specifically tailored to your model's 15 features.

def calculate_entropy(text):
    """Calculates the Shannon entropy of a string."""
    if not text:
        return 0
    prob = [float(text.count(c)) / len(text) for c in dict.fromkeys(list(text))]
    entropy = -sum([p * math.log(p) / math.log(2.0) for p in prob])
    return entropy

def extract_features(url):
    """
    Extracts the 15 features your XGBoost model was trained on.
    The order of features in the returned list is crucial.
    """
    features = []
    
    # 1. url_length
    features.append(len(url))

    # 2. count_dot
    features.append(url.count('.'))

    # 3. count_hyphen
    features.append(url.count('-'))

    # 4. count_at
    features.append(url.count('@'))

    # 5. count_question
    features.append(url.count('?'))

    # 6. count_equal
    features.append(url.count('='))

    # 7. count_percent
    features.append(url.count('%'))

    # 8. count_slash
    features.append(url.count('/'))

    # 9. https (1 if yes, 0 if no)
    parsed_url = urlparse(url)
    features.append(1 if parsed_url.scheme == 'https' else 0)

    # 10. entropy
    features.append(calculate_entropy(url))
    
    # Extract domain-related features using tldextract
    extracted = tldextract.extract(url)
    domain = extracted.domain
    subdomain = extracted.subdomain
    tld = extracted.suffix

    # 11. domain_length
    features.append(len(domain))

    # 12. subdomain_length
    features.append(len(subdomain))

    # 13. tld_length
    features.append(len(tld))
    
    # 14. has_suspicious_word
    suspicious_words = ['login', 'secure', 'bank', 'account', 'update', 'verify', 'signin', 'password']
    has_word = 0
    for word in suspicious_words:
        if word in url.lower():
            has_word = 1
            break
    features.append(has_word)
    
    # 15. has_ip (checks if the netloc is an IP address)
    # A simple regex to check for IP address format in the domain part
    ip_pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    features.append(1 if ip_pattern.match(parsed_url.netloc) else 0)

    # Return as a numpy array, which the model expects
    return np.array(features)


# --- API ENDPOINT ---
@app.route('/predict', methods=['POST'])
def predict():
    """
    API endpoint to predict if a URL is phishing.
    """
    if model is None:
        return jsonify({'error': 'Model not loaded. Please check the server logs.'}), 500

    try:
        data = request.get_json()
        url_to_check = data.get('url')

        if not url_to_check:
            return jsonify({'error': 'URL not provided'}), 400

        # --- NEW: WHITELIST CHECK ---
        # First, check if the domain is on our trusted list.
        try:
            # Extract the registered domain (e.g., 'wikipedia.org' from 'en.wikipedia.org')
            extracted = tldextract.extract(url_to_check)
            main_domain = f"{extracted.domain}.{extracted.suffix}"
            
            if main_domain in WHITELIST:
                print(f"URL: {url_to_check}, Status: legitimate (from whitelist)")
                return jsonify({'status': 'legitimate', 'probability': 0.0})
        except Exception as e:
            # If tldextract fails, proceed to the model but log the error
            print(f"Could not perform whitelist check on {url_to_check}: {e}")

        # 1. Extract the 15 features from the URL
        features = extract_features(url_to_check)
        
        # 2. Reshape features and create DMatrix for XGBoost
        dmatrix = xgb.DMatrix(features.reshape(1, -1), feature_names=FEATURE_NAMES)

        # 3. Make a prediction
        prediction_prob = model.predict(dmatrix)
        prediction = 1 if prediction_prob[0] > 0.5 else 0

        # 4. Determine the status
        status = 'phishing' if prediction == 1 else 'legitimate'
        
        print(f"URL: {url_to_check}, Prediction Probability: {prediction_prob[0]:.4f}, Final Status: {status}")

        # 5. Return the result
        return jsonify({'status': status, 'probability': float(prediction_prob[0])})

    except Exception as e:
        print(f"An error occurred during prediction: {e}")
        return jsonify({'error': 'An internal error occurred.'}), 500

if __name__ == '__main__':
    # Setting debug=True is helpful for development to get more detailed errors.
    app.run(debug=True)

