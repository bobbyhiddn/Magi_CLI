import os
import tempfile
import click
from flask import Flask, render_template_string, request
from git import Repo

@click.command()
@click.argument('repo_url', required=True)
def astral_realm(repo_url):
    """Clone a remote repository, start a local server, and populate a webpage with the repository's files. """
    repo_dir = tempfile.mkdtemp()
    Repo.clone_from(repo_url, repo_dir)
    app.config['REPO_DIR'] = repo_dir
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
                #editor {
                    position: absolute;
                    top: 50px;
                    right: 0;
                    bottom: 0;
                    left: 0;
                }
            </style>
        </head>
        <body>
            <select id="file-select">
                {% for file in files %}
                <option value="{{ file }}">{{ file }}</option>
                {% endfor %}
            </select>
            <div id="editor"></div>
            <button id="save-button">Save</button>
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