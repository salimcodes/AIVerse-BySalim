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

@app.route('/option/1', methods = ['GET'])
def index_one():
    return render_template("index-1.html")

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




# Option 3
@app.route('/option/3', methods=['GET'])
def index_three():
    return render_template('index-3.html')

@app.route('/option/3', methods=['POST'])
def index_post_three():
    from azure.core.credentials import AzureKeyCredential
    from azure.ai.textanalytics import (
        TextAnalyticsClient,
        ExtractSummaryAction
    ) 
    original_text = request.form['text']
    document = [original_text]

    
    poller = client.begin_analyze_actions(
        document,
        actions=[
            ExtractSummaryAction(max_sentence_count=4)
        ],
    )

    document_results = poller.result()
    for result in document_results:
        extract_summary_result = result[0]  # first document, first result
        summary = ([sentence.text for sentence in extract_summary_result.sentences])

    return render_template(
        'results-3.html', 
        document = document,
        summary = summary
        )


#Option 4

import os
import time
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
cog_key = os.environ['COG_SERVICE_KEY']
cog_endpoint = os.environ['COG_SERVICE_ENDPOINT']

@app.route('/option/4', methods=['GET'])
def index_four():
    return render_template('index-4.html')

def GetTextRead(image_data):
    global cv_client
    credential = CognitiveServicesCredentials(cog_key)
    cv_client = ComputerVisionClient(cog_endpoint, credential)


    read_op = cv_client.read_in_stream(image_data, raw=True)
    operation_location = read_op.headers["Operation-Location"]
    operation_id = operation_location.split("/")[-1]

    while True:
        read_results = cv_client.get_read_result(operation_id)
        if read_results.status not in [OperationStatusCodes.running, OperationStatusCodes.not_started]:
            break
        time.sleep(1)

    extracted_text = ""

    if read_results.status == OperationStatusCodes.succeeded:
        for page in read_results.analyze_result.read_results:
            for line in page.lines:
                extracted_text += line.text + ".  \n"

    return extracted_text

from werkzeug.utils import secure_filename
# Define the directory where uploaded files will be stored
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'tiff', 'bmp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route to handle file uploads and perform OCR
@app.route('/option/4', methods=['POST'])
def index_post_four():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        return redirect(request.url)

    if file and allowed_file(file.filename):
        # Save the uploaded file to the UPLOAD_FOLDER
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        
        # Add your OCR logic here to extract text from the uploaded file
        # Example:
        extracted_text = GetTextRead(filename)  # Replace with your OCR function
        return render_template('results-4.html', extracted_text=extracted_text)
    else:
        return 'Invalid file format! Allowed formats are: pdf, png, jpg, jpeg, gif, tiff, bmp'

'''
import os
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Define the directory where uploaded files will be stored
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route to display the file upload form
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle file uploads
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return 'File uploaded successfully!'
    else:
        return 'Invalid file format! Allowed formats are: txt, pdf, png, jpg, jpeg, gif'

if __name__ == '__main__':
    app.run(debug=True)

'''



if __name__ == '__main__':
    app.run(debug=True)


