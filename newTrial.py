from flask import Flask, request, render_template, url_for
from werkzeug.utils import secure_filename
from PIL import Image
import google.generativeai as genai
import markdown
from bs4 import BeautifulSoup
import os
import re
from html import escape

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

genai.configure(api_key="AIzaSyC-nBrOODqs8BSt4G01LaOQS1JajxdeHRk")

instruction = ("You are a Text extractor, your work is to extract the given text in image and return it in a way that user have written")

instruction_check = ("You are a Assignment checker. You will be provided with image which will contain assignment."
              "Assignment will be handwritten so there may be untidy writting"
            "You have to check for spelling mistakes, grammar (only for literature) and facts to grade the assignment. "
           " Total weightage to a single assignment question is 10 marks or depending on what user specifies so depending on number of mistakes a student makes give him marks and feedback."
           " You have to return text that will look like a human teacher have passed."
           " Also suggest online resources and videos with links which will help in minimizing made mistakes. Pay attention to user input text if given")

model = genai.GenerativeModel("models/gemini-2.0-flash-exp",system_instruction=instruction)
model_text = genai.GenerativeModel("models/gemini-2.0-flash-exp",system_instruction=instruction_check)

def convert_urls_to_links(text):
    paragraphs = text.split('\n\n')
    processed_paragraphs = []
    
    for paragraph in paragraphs:
        lines = paragraph.splitlines()
        processed_lines = []
        
        for line in lines:
            url_pattern = r'(https?://\S+)'
            def replace_with_link(match):
                url = match.group(1)
                return f'<a href="{escape(url)}" target="_blank" class="resource-link">{escape(url)}</a>'
            line = re.sub(url_pattern, replace_with_link, line)
            processed_lines.append(line)
            
        processed_paragraphs.append("<br>".join(processed_lines))
    
    return "<br><br>".join(processed_paragraphs)

def clean_gemini_text(gemini_response):
    html_output = markdown.markdown(gemini_response)
    soup = BeautifulSoup(html_output, 'html.parser')
    plain_text = soup.get_text()
    plain_text = plain_text.replace('\n', '\n')
    plain_text = plain_text.replace("<p>", "").replace("</p>", " ")
    plain_text = plain_text.replace("<br/>", " ")
    return plain_text

def check_text_with_gemini(image):
    response = model.generate_content([image, "This is the assignment"])
    res = clean_gemini_text(response.text)
    return convert_urls_to_links(res)  # Process the text to make URLs clickable

def gem_check(text):
    respon = model_text.generate_content(text)
    resp = clean_gemini_text(respon.text)
    return convert_urls_to_links(resp)  # Process the text to make URLs clickable

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signInPage')
def signInPage():
    return render_template('SignIn.html')

@app.route('/logInPage')
def logInPage():
    return render_template('LogIn.html')

@app.route('/chat_main')
def chat_main():
    return render_template('main_chat.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "No file part", 400

    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    try:
        image = Image.open(file)
        checked_text = check_text_with_gemini(image)
        return checked_text
    except Exception as e:
        return f"Error processing image: {e}", 500

@app.route('/uptext', methods=['POST'])
def uptext():
    texted = request.data.decode('utf-8')
    if texted:
        return gem_check(texted)
    return "NO DATA RECEIVED", 400

if __name__ == '__main__':
    app.run(debug=True)
