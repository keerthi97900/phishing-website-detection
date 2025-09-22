document.addEventListener('DOMContentLoaded', () => {
    const checkUrlBtn = document.getElementById('checkUrlBtn');
    const resultDiv = document.getElementById('result');
    const currentUrlP = document.getElementById('currentUrl');
    
    // The URL for your Flask backend's prediction endpoint
    const backendUrl = 'http://127.0.0.1:5000/predict';

    // Get the current tab's URL and display it in the popup.
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs && tabs.length > 0) {
            const url = tabs[0].url;
            // Display only a portion of the URL if it's too long
            currentUrlP.textContent = url.length > 50 ? url.substring(0, 50) + '...' : url;
            currentUrlP.title = url; // Show full URL on hover
        } else {
            currentUrlP.textContent = 'Could not get URL.';
            checkUrlBtn.disabled = true;
        }
    });

    // Handle the button click event
    checkUrlBtn.addEventListener('click', () => {
        // Disable button to prevent multiple clicks
        checkUrlBtn.disabled = true;
        checkUrlBtn.textContent = 'Checking...';

        // Reset and show the result div with a "checking" message
        resultDiv.textContent = 'Analyzing URL...';
        resultDiv.className = 'result-container result-checking';

        // Get the active tab's URL again to ensure it's the right one
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (chrome.runtime.lastError || !tabs || tabs.length === 0) {
                displayError('Could not access the current tab.');
                return;
            }

            const currentUrl = tabs[0].url;
            
            // Make sure the URL is a valid http/https URL before sending
            if (!currentUrl.startsWith('http')) {
                displayError('Cannot check local or special URLs (e.g., chrome://).');
                return;
            }

            // Send the URL to the backend for prediction
            fetch(backendUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: currentUrl }),
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server responded with status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    displayError(data.error);
                } else {
                    displayResult(data.status);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                displayError('Cannot connect to the backend server. Is it running?');
            })
            .finally(() => {
                // Re-enable the button after the process is complete
                checkUrlBtn.disabled = false;
                checkUrlBtn.textContent = 'Check URL';
            });
        });
    });

    /**
     * Displays the prediction result in the UI.
     * @param {string} status - The status from the backend ('legitimate' or 'phishing').
     */
    function displayResult(status) {
        if (status === 'phishing') {
            resultDiv.textContent = 'Warning! This site is likely a phishing attempt.';
            resultDiv.className = 'result-container result-phishing';
        } else {
            resultDiv.textContent = 'This site appears to be legitimate.';
            resultDiv.className = 'result-container result-legitimate';
        }
    }

    /**
     * Displays an error message in the UI.
     * @param {string} message - The error message to display.
     */
    function displayError(message) {
        resultDiv.textContent = `Error: ${message}`;
        resultDiv.className = 'result-container result-error';
        checkUrlBtn.disabled = false;
        checkUrlBtn.textContent = 'Check URL';
    }
});
