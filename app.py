from dotenv import load_dotenv
load_dotenv()
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from openai import AsyncOpenAI
import spacy

# Initialize Spacy and OpenAI clients
nlp = spacy.load("en_core_web_sm")
client = AsyncOpenAI(api_key="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")

# Initialize Flask app
app = Flask(__name__)

# custom gpt messages
# def generate_gpt_message(topic, text):
#     if topic == "coding":
#         return [
#             {"role": "system", "content": "You are a helpful assistant."},
#             {"role": "user", "content": f"Explain the following code in simple terms: {text}"}
#         ]
#     elif topic == "documentation":
#         return [
#             {'role': 'system', 'content': "You will now clean up and clarify the following documentation section. Make sure to explain technical terms, elaborate on complex points, and organize the content for better understanding."},
#             {'role': 'user', 'content': f"Please clean up and clarify this documentation, focusing on making it more understandable and user-friendly, include examples, structure it as json format, add naming: {text}"}
#         ]
#     elif topic == "news":
#         return [
#             {"role": "system", "content": "You are a helpful assistant."},
#             {"role": "user", "content": f"Provide a brief summary of this news article: {text}"}
#         ]
#     else:
#         return [
#             {"role": "system", "content": "You are a helpful assistant."},
#             {"role": "user", "content": f"Provide an overview of the following text: {text}"}
#         ]

# Route to process HTML content
async def process_html():
    data = request.json
    html_content = data['html']
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove unnecessary tags
    for tag in soup(["script", "style", "svg", "path", "img", "nav", "footer", "aside", "sidebar", "button"]):
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
    # topic = await get_openai_topics(refined_text)
    # summarized_data = await get_openai_summary(structured_data, topic)

    response = {
        'structured_data': structured_data,
        # 'summarized_data': summarized_data,
        # 'topic': topic
    }

    return jsonify(response)
# Async function to summarize with AI
# async def get_openai_summary(structured_data, topic):
#     summarized_data = {}
#     for heading, text in structured_data.items():
#         messages = generate_gpt_message(topic, text)
#         chat_completion = await client.chat.completions.create(
#             messages=messages,
#             model="gpt-3.5-turbo-1106",
#             max_tokens=4000
#         )
#         summary = chat_completion.choices[0].message.content
#         summarized_data[heading] = summary

#     return summarized_data

# Async function to define topics with AI
async def get_openai_topics(text):
    truncated_text = ' '.join(text.split()[:750])  # Truncate to approx. 1000 tokens

    chat_completion = await client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Your task is to define the topic based on provided content in only one word. Topics include documentation, news, code, education."},
            {"role": "user", "content": f"Define the topic, topics are only these three: documentation, news, education. based on this content in: {truncated_text}"}
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

app.add_url_rule('/process', view_func=process_html, methods=['POST'])

if __name__ == '__main__':
    app.run(debug=True)
