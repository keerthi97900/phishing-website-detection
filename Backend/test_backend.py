import requests # A library for making HTTP requests

# The URL where your Flask server is running
SERVER_URL = 'http://127.0.0.1:5000/predict'

def check_url(url_to_test):
    """Sends a URL to the Flask server and prints the response."""
    print(f"\nChecking URL: {url_to_test}")

    # The data we need to send, in JSON format
    payload = {'url': url_to_test}
    
    try:
        # Make the POST request to our server's /predict endpoint
        response = requests.post(SERVER_URL, json=payload)

        # Check if the request was successful
        if response.status_code == 200:
            # Get the JSON data from the response
            result = response.json()
            status = result.get('status', 'N/A')
            probability = result.get('probability', 0)
            
            # Print the results in a user-friendly way
            print("---- Prediction Result ----")
            print(f"  Status: {status.upper()}")
            print(f"  Phishing Probability: {probability:.2%}")
            print("---------------------------")
        else:
            # If something went wrong on the server
            print(f"Error: Server responded with status code {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.ConnectionError:
        # If we can't connect to the server at all
        print("\n--- CONNECTION ERROR ---")
        print("Could not connect to the server.")
        print("Please make sure your Flask server (`app.py`) is running in another terminal.")
        print("------------------------")
        return False
    
    return True

if __name__ == '__main__':
    print("--- Backend Test Client ---")
    print("Enter a URL to check, or type 'exit' to quit.")
    
    # Loop forever to allow testing multiple URLs
    while True:
        user_input = input("> ")
        if user_input.lower() in ['exit', 'quit']:
            break
        if not user_input:
            continue
        
        # Add a default scheme if one isn't present
        if not user_input.startswith(('http://', 'https://')):
            url_to_check = 'http://' + user_input
        else:
            url_to_check = user_input
        
        if not check_url(url_to_check):
            break
