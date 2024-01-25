from dotenv import load_dotenv
load_dotenv()
import os
import asyncio
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from openai import AsyncOpenAI
import openai
import spacy

# Initialize Spacy and OpenAI clients
nlp = spacy.load("en_core_web_sm")
client = AsyncOpenAI(api_key="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")

# Initialize Flask app
app = Flask(__name__)


# Route to process HTML content
@app.route('/process', methods=['POST'])
def process_html():
    data = request.json
    html_content = data['html']
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove unnecessary tags
    for tag in soup(["script", "style", "svg", "path", "img", "nav", "footer", "header", "aside", "sidebar", "button"]):
        tag.decompose()

    structured_data = {"General": []}
    processed_elements = set()

    for element in soup.find_all(True):
        if element in processed_elements:
            continue
        if element.name in ['p', 'div', 'section']:
            text = element.get_text(" ", strip=True)
            if text:
                structured_data["General"].append(text)
                processed_elements.update(element.find_all(True))

    combined_text = ' '.join(structured_data["General"])
    refined_text = remove_duplicate_sentences(combined_text)
    structured_data["General"] = refined_text

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    summarized_data = loop.run_until_complete(get_openai_summary(structured_data))
    loop.close()

    response = {
        'structured_data': structured_data,
        'summarized_data': summarized_data
    }

    return jsonify(response)

# Async function to summarize with AI
async def get_openai_summary(structured_data):
    summarized_data = {}
    for heading, text in structured_data.items():
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"2+2"}
            ],
            model="gpt-3.5-turbo-1106",
            max_tokens=200
        )
        summary = chat_completion.choices[0].message.content
        summarized_data[heading] = summary

    return summarized_data

# Async function to define topics with AI
async def get_openai_topics(structured_data):
    # Truncate the text to approximately 1000 tokens
    topics_data = ' '.join(text.split()[:750])
    for heading, text in structured_data.items():
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant. your have to define topic based on provided content in only one word, topic will be documentation, news, code, education"},
                {"role": "user", "content": f"define topic based on provided content, {text}"}
            ],
            model="gpt-3.5-turbo-1106",
            max_tokens=200
        )
        topics = chat_completion.choices[0].message.content
        topics_data[heading] = topics

    return topics_data

# Function to remove duplicate sentences
def remove_duplicate_sentences(text):
    doc = nlp(text)
    sentences = list(doc.sents)
    unique_sentences = []

    for sentence in sentences:
        if not any(sentence.similarity(other) > 0.9 for other in unique_sentences):
            unique_sentences.append(sentence)

    return " ".join(str(sentence) for sentence in unique_sentences)

# Function to optimize text by splitting into chunks
def split_and_optimize_text(text, max_chunk_size=1000):
    paragraphs = text.split('\n')
    optimized_text = []
    current_chunk = ""

    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) > max_chunk_size:
            optimized_text.append(current_chunk.strip())
            current_chunk = ""
        current_chunk += paragraph + '\n'

    if current_chunk:
        optimized_text.append(current_chunk.strip())

    return optimized_text



if __name__ == '__main__':
    app.run(debug=True)
