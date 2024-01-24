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

    structured_data = {"General": []}
    processed_elements = set()  # Track processed elements

    for element in soup.find_all(True):
        if element in processed_elements:
            continue  # Skip already processed elements

        if element.name in ['p', 'div', 'section']:
            text = element.get_text(" ", strip=True)
            if text:
                structured_data["General"].append(text)
                processed_elements.update(element.find_all(True))  # Mark child elements as processed

    # Clean and filter text in "General"
    cleaned_text = []
    for text in structured_data["General"]:
        if text not in cleaned_text:  # Avoid duplication
            cleaned_text.append(text)

    structured_data["General"] = ' '.join(cleaned_text)


    # Debug print to check how the data is structured
    # print(structured_data)
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