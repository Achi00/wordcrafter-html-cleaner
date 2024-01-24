from dotenv import load_dotenv
load_dotenv()
import os
import asyncio
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process_html():
    data = request.json
    html_content = data['html']
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove unnecessary tags
    for tag in soup(["script", "style", "svg", "path", "img", "nav", "footer", "header", "aside", "sidebar", "button"]):
        tag.decompose()

    structured_data = {}
    current_heading = "General"
    structured_data[current_heading] = []  # Initialize 'General' heading

    for element in soup.find_all(True):
        if element.name in ['h1', 'h2', 'h3']:
            current_heading = element.get_text(strip=True)
            structured_data[current_heading] = []  # Initialize new heading
        elif element.name in ['p', 'div', 'section']:
            text = element.get_text(" ", strip=True)
            if text and text not in structured_data[current_heading]:
                structured_data[current_heading].append(text)

    # Remove empty sections and the 'General' section if it's empty
    unwanted_titles = [""]  # Add any other unwanted titles here
    structured_data = {k: v for k, v in structured_data.items() if v and k not in unwanted_titles}
    # Summarize the content of each section
    # summarized_data = {}
    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    # summarized_data = loop.run_until_complete(get_openai_summary(structured_data))
    # loop.close()

    response = {
        'structured_data': structured_data,
        # 'summarized_data': summarized_data
    }

    return jsonify(response)

# summatize with ai
async def get_openai_summary(structured_data):
    summarized_data = {}
    for heading, texts in structured_data.items():
        full_text = ' '.join(texts)
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": f"Classify the following text into a category such as general, technical, or code in one word: {full_text}"}
            ],
            model="gpt-3.5-turbo-1106",
        )
        summary = chat_completion.choices[0].message.content
        summarized_data[heading] = summary

    return summarized_data

if __name__ == '__main__':
    app.run(debug=True)