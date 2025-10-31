import copy
from dotenv import load_dotenv
import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold, GenerationConfig
from google.ai.generativelanguage_v1beta.types import content

import certifi

load_dotenv()

gemini_api = os.getenv("GEMINI_API")
google_search_api = os.getenv("GOOGLE_SEARCH_API")
whole_web_cse_id = "464ebf0f8c67e4f32"  # custom search engine ID

genai.configure(api_key=gemini_api)

old_response_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The original main sentence from which claims are extracted."
            },
            "claims": {
                "type": "array",
                "description": "A list of claims extracted from the text.",
                "items": {
                    "type": "object",
                    "properties": {
                        "claim": {
                            "type": "string",
                            "description": "The extracted claim in a concise form. Contains MORE info than the (subject, predicate, object) triple"
                        },
                        "span": {
                            "type": "string",
                            "description": "The exact span within the original sentence that expresses the claim."
                        },
                        "subject": {
                            "type": "string",
                            "description": "The subject of the claim."
                        },
                        "predicate": {
                            "type": "string",
                            "description": "The relationship or action connecting the subject and object."
                        },
                        "object": {
                            "type": "string",
                            "description": "The object or result related to the subject in the claim."
                        },
                        "search_query": {
                            "type": "string",
                            "description": "A single search query if the claim is not comparative, two if otherwise"
                        }
                    },
                    "required": ["claim", "span", "subject", "predicate", "object", "search_query"]
                }
            }
        },
        "required": ["text", "claims"]
    }
}

response_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "claim": {
                "type": "string",
                "description": "The extracted claim in a concise form, written as if it came from an article about the subject."
            },
            "span": {
                "type": "string",
                "description": "The exact span within the original text that expresses the claim."
            },
            "subject": {
                "type": "string",
                "description": "The subject of the claim."
            },
            "predicate": {
                "type": "string",
                "description": "The relationship or action connecting the subject and object."
            },
            "object": {
                "type": "string",
                "description": "The object or result related to the subject in the claim."
            },
            "search_query": {
                "type": "string"
            }
        },
        "required": ["claim", "span", "subject", "predicate", "object", "search_query"]
    }
}

# Create the model
generation_config = {
    "temperature": 0,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_schema": response_schema,
    "response_mime_type": "application/json",
}

import json


def process_and_stringify(input_file, output_file):
    with open(input_file, 'r') as f:
        data = json.load(f)

    processed_data = []
    for item in data:
        processed_data.append({
            "input": item["input"],
            "output": json.dumps(item["output"], sort_keys=True)
        })

    with open(output_file, 'w') as f:
        json.dump(processed_data, f, indent=2)


process_and_stringify('train_dataset_simple.json', 'processed_train_dataset.json')
with open('processed_train_dataset.json') as f:
    dataset = json.load(f)


# model training history
history = []

train_validate_ratio = 1 # 2 / 3
train_amount = int(len(dataset) * train_validate_ratio)
validate_amount = len(dataset) - train_amount
train_dataset = dataset[:train_amount]
validate_dataset = dataset[-validate_amount:]

# dynamically add user inputs and model outputs
for item in train_dataset:
    history.append("text_input " + item["input"])
    history.append("output " + item["output"])

# possibly also prompt:  You can also find implicit claims from opposites
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash-lite",
    generation_config=generation_config,
safety_settings={
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE
    }
)

import json
import sys


def get_response(post):
    """
    :param post: The social media post
    :return: string object of chat response
    """

    messages = copy.deepcopy(history)

    messages.append("text_input " + post)
    messages.append("output ")
    response = model.generate_content(messages)
    return response.text


import requests
from newspaper import Article


def google_search(query, api_key, cx, num_results=10):
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "num": num_results
    }
    response = requests.get(search_url, params=params, verify=certifi.where())
    response.raise_for_status()
    search_results = response.json()

    urls = [item["link"] for item in search_results.get("items", [])]
    return urls


def extract_text_from_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, verify=certifi.where())
        response.raise_for_status()

        article = Article(url)
        article.set_html(response.text)
        article.parse()
        return article.text
    except requests.exceptions.RequestException as e:
        print(f"Request failed for {url}: {e}")
        return None


# TODO: make google API look at trusted sites, e.g. specifically search on DOAJ or NYT for links and use their API instead of scraping
import concurrent.futures

def fetch_and_extract(url):
    try:
        return url, extract_text_from_url(url)
    except Exception as e:
        print(f"Error: {e}")
        return url, None

def search_documents(data, field_for_query='search_query'):
    '''

    :param data:
    :return: A dictionary of urls to text and claim tuples
    '''
    queries = [(claim[field_for_query], claim["claim"]) for claim in data]
    all_documents = {}
    for query in queries:
        urls = google_search(query[0], google_search_api, whole_web_cse_id, 3)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(fetch_and_extract, urls)
        all_documents.update({
            url: (text, query[1]) for url, text in results if text})
    return all_documents

def keyword_search_documents(key_words):
    urls = google_search(" ".join(key_words), google_search_api, whole_web_cse_id, 5)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(fetch_and_extract, urls)
    return {url: text for url, text in results if text}