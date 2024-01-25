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
client = AsyncOpenAI(api_key="")

# Initialize Flask app
app = Flask(__name__)


# Can you provide a summary of the key concepts from this documentation? I'm also looking for practical examples, best practices, and any notable insights or advanced tips that can be derived from it.
def generate_gpt_message(topic, text):
    if topic == "coding":
        return f"Explain the following code in simple terms: {text}"
    elif topic == "documentation":
        return [
        {'role': 'system', 'content': "You are about to read a documentation section. Analyze and understand its content thoroughly. Provide a summary and highlight key points, concepts, and any necessary details for a user to understand it effectively."},
        {'role': 'system', 'content': "Here is the documentation: {text}."},
        {'role': 'assistant', 'content': "Provide a summary of the documentation here, focusing on key points, essential concepts, necessary details and examples."},
        {'role': 'user', 'content': "Based on the documentation, what are the main steps or procedures one should follow when using this software? What are the best practices and common pitfalls to be aware of? What are the best practices and examples? what are common mistakes?"},
    ]
    elif topic == "news":
        return f"Provide a brief summary of this news article: {text}"
    # Add more conditions for other topics
    else:
        return f"Provide an overview of the following text: {text}"

# Route to process HTML content
async def process_html():
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

    # Asynchronously get the topic and summary
    topic = await get_openai_topics(refined_text)
    summarized_data = await get_openai_summary(structured_data)

    response = {
        'structured_data': structured_data,
        'summarized_data': summarized_data,
        'topic': topic
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
# Async function to define topics with AI
async def get_openai_topics(text):
    truncated_text = ' '.join(text.split()[:750])  # Truncate to approx. 1000 tokens

    chat_completion = await client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Your task is to define the topic based on provided content in only one word. Topics include documentation, news, code, education."},
            {"role": "user", "content": f"Define the topic, topics are documentation, news, education, based on this content in: {truncated_text}"}
        ],
        model="gpt-3.5-turbo-1106",
        max_tokens=200
    )
    topic = chat_completion.choices[0].message.content.strip()
    return topic


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

app.add_url_rule('/process', view_func=process_html, methods=['POST'])

if __name__ == '__main__':
    app.run(debug=True)
