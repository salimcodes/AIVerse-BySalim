import requests, os, uuid, json
from dotenv import load_dotenv
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()
from flask import Flask, redirect, url_for, request, render_template, session

app = Flask(__name__)



@app.route('/')
def index():
    # Render the HTML template
    return render_template('index.html')
    
# Option 1 

@app.route('/option/<int:option_number>', methods = ['GET'])
def index_one(option_number):
    # Generate the filename based on the option_number (e.g., 'index-1.html')
    filename = f'index-{option_number}.html'
    return render_template(filename)

@app.route('/option/1', methods=['POST'])
def index_post_one():
    # Read the values from the form
    original_text = request.form['text']
    target_language = request.form['language']

    # Load the values from .env
    key = os.environ['KEY']
    endpoint = os.environ['ENDPOINT']
    location = os.environ['LOCATION']

    # Indicate that we want to translate and the API version (3.0) and the target language
    path = '/translate?api-version=3.0'
    # Add the target language parameter
    target_language_parameter = '&to=' + target_language
    # Create the full URL
    constructed_url = endpoint + path + target_language_parameter

    # Set up the header information, which includes our subscription key
    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    # Create the body of the request with the text to be translated
    body = [{ 'text': original_text }]

    # Make the call using post
    translator_request = requests.post(constructed_url, headers=headers, json=body)
    # Retrieve the JSON response
    translator_response = translator_request.json()
    # Retrieve the translation
    translated_text = translator_response[0]['translations'][0]['text']

    # Call render template, passing the translated text,
    # original text, and target language to the template
    return render_template(
        'results-1.html',
        translated_text=translated_text,
        original_text=original_text,
        target_language=target_language
    )



# Option 2


language_key = os.getenv("LANGUAGE_KEY")
language_endpoint = os.getenv("LANGUAGE_ENDPOINT")
def authenticate_client():
    ta_credential = AzureKeyCredential(language_key)
    text_analytics_client = TextAnalyticsClient(
            endpoint=language_endpoint, 
            credential=ta_credential)
    return text_analytics_client

client = authenticate_client()

@app.route('/option/2', methods=['GET'])
def index_two():
    return render_template('index-2.html')

@app.route('/option/2', methods=['POST'])
def index_post_two():
    # Read the values from the form
    original_text = request.form['text']
    documents = [original_text]


    result = client.analyze_sentiment(documents, show_opinion_mining=True)
    doc_result = [doc for doc in result if not doc.is_error]

    positive_reviews = [doc for doc in doc_result if doc.sentiment == "positive"]
    negative_reviews = [doc for doc in doc_result if doc.sentiment == "negative"]

    positive_mined_opinions = []
    mixed_mined_opinions = []
    negative_mined_opinions = []

    for document in doc_result:
        sentiment = document.sentiment
        positive_confidence_scores = document.confidence_scores.positive
        negative_confidence_scores = document.confidence_scores.negative
        neutral_confidence_scores = document.confidence_scores.neutral
    return render_template(
        'results-2.html', 
        sentiment = sentiment, 
        positive_confidence_scores = positive_confidence_scores,
        negative_confidence_scores = negative_confidence_scores,
        neutral_confidence_scores = neutral_confidence_scores
        )



if __name__ == '__main__':
    app.run(debug=True)
