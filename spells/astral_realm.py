# Here is the full revised version of your code with the image generation function.

import os
import tempfile
import click
from flask import Flask, render_template_string, request
from git import Repo
import openai
import requests
from PIL import Image
from io import BytesIO

# Function to generate an image using DALL-E API
def generate_image(prompt):
    response = openai.Image.create(
        model="image-alpha-001",
        prompt=prompt,
        n=1,
        # size="500x500",
        response_format="url"
    )
    image_url = response['data'][0]['url']
    image_data = requests.get(image_url).content
    image = Image.open(BytesIO(image_data))
    return image

@click.command()
@click.argument('repo_url', required=True)
def astral_realm(repo_url):
    """Clone a remote repository, start a local server, and populate a webpage with the repository's files. """
    repo_dir = tempfile.mkdtemp()
    Repo.clone_from(repo_url, repo_dir)
    app.config['REPO_DIR'] = repo_dir

    # Generate the background image
    img = generate_image("An astromage's studyroom. Books about the topics an astromage would study. Esoteric, arcane, stone, and glass. Semi-realistic, alchemist workshop. In the style of dungeons and dragons.")

    # Save the image to the static folder of the Flask app
    img_path = os.path.join('static', 'background.png')
    os.makedirs(os.path.dirname(img_path), exist_ok=True)
    img.save(img_path)

    app.run(debug=True)

# Flask functionality

app = Flask(__name__)

@app.route('/')
def index():
    files = []
    for foldername, subfolders, filenames in os.walk(app.config['REPO_DIR']):
        for filename in filenames:
            files.append(os.path.join(foldername, filename))
    return render_template_string('''
    <!doctype html>
    <html>
        <head>
            <title>Repository Files</title>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/ace/1.4.12/ace.js"></script>
            <style>
                body {
                    display: flex;
                    flex-direction: column;
                    height: 100vh;
                    margin: 0;
                    background-image: url('static/background.png');
                    background-size: 100% 100%;  /* Changed this line */
                    background-repeat: no-repeat; /* Added this line */
                }

                #banner {
                    height: 50px;
                    background-color: #eee;
                    padding: 10px;
                    box-sizing: border-box;
                }
                #main {
                    flex-grow: 1;
                    display: flex;
                }
                #sidebar {
                    width: 200px;
                    padding: 10px;
                    box-sizing: border-box;
                }
                #editor {
                    flex-grow: 1;
                }
            </style>
        </head>
        <body>
            <div id="banner">
                <img src="/static/background.png" alt="Background Image" style="width:100%;">
            </div>


            <div id="banner">
                <select id="file-select">
                    {% for file in files %}
                    <option value="{{ file }}">{{ file }}</option>
                    {% endfor %}
                </select>
            </div>
            <div id="main">
                <div id="sidebar">
                    <button id="save-button">Save</button>
                </div>
                <div id="editor"></div>
            </div>
            <script>
                var editor = ace.edit("editor");
                editor.setTheme("ace/theme/monokai");
                editor.session.setMode("ace/mode/javascript");
                var select = document.getElementById('file-select');
                var button = document.getElementById('save-button');
                
                // Load the content of the file into the editor when it's selected
                select.addEventListener('change', function() {
                    fetch('/file/' + select.value)
                        .then(response => response.text())
                        .then(data => editor.setValue(data));
                });
                
                // Save the content of the editor to the file when the save button is clicked
                button.addEventListener('click', function() {
                    fetch('/file/' + select.value, {
                        method: 'POST',
                        body: editor.getValue(),
                        headers: {
                            'Content-Type': 'text/plain'
                        }
                    });
                });
            </script>
        </body>
    </html>
    ''', files=files)

@app.route('/file/<path:file_path>', methods=['GET', 'POST'])
def file(file_path):
    absolute_path = os.path.join(app.config['REPO_DIR'], file_path)
    if request.method == 'GET':
        with open(absolute_path, 'r') as file:
            return file.read()
    elif request.method == 'POST':
        with open(absolute_path, 'w') as file:
            file.write(request.data.decode())
        return '', 204
    
# Run the Flask app
if __name__ == '__main__':
    astral_realm()
