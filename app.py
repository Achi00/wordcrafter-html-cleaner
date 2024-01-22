from flask import Flask, request, jsonify
from bs4 import BeautifulSoup

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

    response = {
        'structured_data': structured_data
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
