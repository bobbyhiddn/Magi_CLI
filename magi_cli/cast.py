#!/usr/bin/env python3

import click # type: ignore
import subprocess
import sys
import os
import shutil
import inspect
import re
import fnmatch
import openai # type: ignore
import glob
import requests
from PIL import Image, ImageDraw, ImageOps
from io import BytesIO
from datetime import datetime
from pathlib import Path
from click import Context # type: ignore
from dotenv import load_dotenv # type: ignore

# Load the Openai API key
# This can also be done by setting the OPENAI_API_KEY environment variable manually.
# load_dotenv() # Uncomment this line if you want to load the API key from the .env file
api_key = os.getenv("OPENAI_API_KEY")

# Set the API key for the OpenAI package through .env file or API key path
# You can also set it by using export OPENAI_API_KEY=<your-api-key> in the terminal.
openai.api_key = api_key
# openai.api_key_path = ".api"


# Non-click functions

def execute_bash_file(filename):
    subprocess.run(["bash", filename], check=True)

def execute_python_file(filename):
    subprocess.run([sys.executable, filename], check=True)

def execute_spell_file(spell_file):
    tome_dir = ".tome"

    # Check if the spell_file starts with the tome_dir
    if not spell_file.startswith(tome_dir):
        spell_file_path = os.path.join(tome_dir, f"{spell_file}.spell")
    else:
        spell_file_path = f"{spell_file}.spell"

    # Check if the spell_file exists in the tome_dir
    if not os.path.exists(spell_file_path):
        # Try to find the spell_file without the tome_dir prefix
        spell_file_path = os.path.join(tome_dir, f"{spell_file.replace('.tome/', '')}.spell")

    if not os.path.exists(spell_file_path):
        click.echo(f"Could not find {spell_file}.spell in .tome directory.")
        return

    with open(spell_file_path, 'r') as file:
        lines = file.readlines()

    for line in lines:
        os.system(line.strip())

# Function to send a message to the OpenAI chatbot model and return its response
def send_message(message_log):
    # Use OpenAI's ChatCompletion API to get the chatbot's response
    response = openai.ChatCompletion.create(
        model="gpt-4",  # The name of the OpenAI chatbot model to use
        messages=message_log,   # The conversation history up to this point, as a list of dictionaries
        max_tokens=3800,        # The maximum number of tokens (words or subwords) in the generated response
        stop=None,              # The stopping sequence for the generated response, if any (not used here)
        temperature=0.7,        # The "creativity" of the generated response (higher temperature = more creative)
    )

    # Find the first response from the chatbot that has text in it (some responses may not have text)
    for choice in response.choices:
        if "text" in choice:
            return choice.text

    # If no response with text is found, return the first response's content (which may be empty)
    return response.choices[0].message.content

# Function to generate an image using DALL-E API
def generate_image(prompt):
    response = openai.Image.create(
        model="image-alpha-001",
        prompt=prompt,
        n=1,
        size="256x256",
        response_format="url"
    )
    image_url = response['data'][0]['url']
    image_data = requests.get(image_url).content
    image = Image.open(BytesIO(image_data))
    return image

# Function to create a circular mask
def create_circular_mask(image):
    width, height = image.size
    mask = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, width, height), fill=255)
    return mask


@click.command()
@click.argument('input', nargs=-1)
def cast(input):
    input = " ".join(input)  # join input arguments into one string if there are multiple

    if input in cli.list_commands(ctx=None):
        cli()  # type: ignore
    elif os.path.isfile(input):  # Check if file exists
        if input.endswith(".py"):  # If it's a Python script
            execute_python_file(input)  # execute the Python script
        elif input.endswith(".spell"):  # If it's a spell file
            execute_spell_file(input.replace(".spell", ""))  # execute the spell
        else:  # if it's not a Python script or a spell file
            cli()  # type: ignore
    else:
        cli()  # type: ignore
        
@click.group()
@click.pass_context
def cli(ctx):
    """A Python CLI for casting spells."""
    pass

@click.command()
def necromancy():
    """Start a session that keeps a memory of deleted files."""
    path = ".graveyard"
    try:
        os.mkdir(path)
    except FileExistsError:
        click.echo("The dark energies swirl around you... A graveyard already lies here.")
    else:
        click.echo("You weave the spell and a graveyard appears, ready to accept the spirits of the deceased files.")

@click.command()
@click.argument('path', required=True)
def fireball(path):
    """Deletes a directory or file."""
    graveyard_path = ".graveyard"
    if os.path.exists(path):
        click.echo(f"Your hands tremble as you draw upon the arcane energies...\n")

        # Check whether the path is a file or a directory
        if os.path.isfile(path):
            confirmation_prompt = "Are you sure you want to continue? A target sent to the graveyard is as dead as can be."
        elif os.path.isdir(path):
            confirmation_prompt = "You are about to incinerate a directory and everything within it, sending it to the graveyard. Are you sure you want to continue?"
        else:
            confirmation_prompt = "Are you sure you want to continue? A target sent to the graveyard is as dead as can be."
        
        if click.confirm(confirmation_prompt, abort=True):
            click.echo("You cast the spell and a fireball erupts from your hands, engulfing the target in flames...")
            click.echo("When the smoke clears, nothing remains but cinder and ash.")
            destination_path = os.path.join(graveyard_path, os.path.basename(path))
            shutil.move(path, destination_path)

            # Clean up the graveyard if it has more than 13 files
            files_in_graveyard = os.listdir(graveyard_path)
            if len(files_in_graveyard) > 13:
                files_in_graveyard.sort(key=lambda x: os.path.getmtime(os.path.join(graveyard_path, x)))
                os.remove(os.path.join(graveyard_path, files_in_graveyard[0]))
    else:
        click.echo(f"Your fireball fizzles... The target at {path} does not exist. Even in the arcane arts, one cannot destroy what is already absent.")

@click.command()
@click.argument('search_term', required=False)
def divine(search_term):
    """List the directory contents with detailed information, or find a file anywhere below the root directory, searching through child directories, and echo its path."""
    if search_term:
        click.echo(f"You cast your senses into the ether, seeking knowledge of the realm...\n")
        for root, dirs, files in os.walk('.'):  # Start search from the root directory
            for file in files:
                if fnmatch.fnmatch(file, f'*{search_term}*'):  # If the file name contains the search term
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    file_permissions = oct(os.stat(file_path).st_mode)[-3:]
                    file_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                    click.echo(f"{file_path}\tSize: {file_size} bytes\tPermissions: {file_permissions}\tLast Modified: {file_modified}")
    else:
        # If no search term was supplied, the function behaves as before
        click.echo(f"You cast your senses into the ether, seeking knowledge of the realm...\n")
        for file in os.listdir("."):
            file_path = os.path.join(".", file)
            file_size = os.path.getsize(file_path)
            file_permissions = oct(os.stat(file_path).st_mode)[-3:]
            file_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
            click.echo(f"{file}\tSize: {file_size} bytes\tPermissions: {file_permissions}\tLast Modified: {file_modified}")

@click.command()
@click.argument('spirit', required=False)
def raise_dead(spirit=None):
    """Restore a spirit from the graveyard."""
    if spirit:
        source_path = os.path.join(".graveyard", spirit)
        if os.path.exists(source_path):
            destination_path = os.path.join(".", "undead_" + spirit)
            shutil.move(source_path, destination_path)
            click.echo(f"The spirit of {spirit} has been restored to this realm, now known as undead_{spirit}.")
        else:
            click.echo("That spirit is not in this graveyard...")
    else:
        click.echo("The spirits in the graveyard are:")
        for file in os.listdir(".graveyard"):
            click.echo(file)
        click.echo("Which spirit would you like to raise?")
        spirit = click.prompt("Spirit name", type=str)
        source_path = os.path.join(".graveyard", spirit)
        if os.path.exists(source_path):
            destination_path = os.path.join(".", "undead_" + spirit)
            shutil.move(source_path, destination_path)
            click.echo(f"The spirit of {spirit} has been restored to this realm, now known as undead_{spirit}.")

@click.command()
@click.argument('num_commands', type=int, required=True)
@click.argument('spell_file', required=True)
def spellcraft(num_commands, spell_file):
    """Create a macro spell and store it in .tome."""
    tome_dir = ".tome"

    # If .tome directory does not exist, create it
    if not os.path.exists(tome_dir):
        os.mkdir(tome_dir)

    # Prompt the user for a description
    description = click.prompt("Enter a description for the macro spell")

    # Create a list to store the entered commands
    entered_commands = []

    # Gather all available command names
    all_spells = [command.name for name, command in inspect.getmembers(sys.modules[__name__]) if isinstance(command, click.core.Command)]

    # Prompt the user to enter the desired commands
    for i in range(num_commands):
        valid_command = False
        while not valid_command:
            entered_command = input(f"Enter command {i + 1}: ")
            # Check if the entered command is valid
            if entered_command.split()[0] in all_spells:
                valid_command = True
                entered_commands.append(entered_command)
            else:
                print(f"The command '{entered_command.split()[0]}' is not recognized. Please enter a valid command.")

    # Write the description and entered commands to the specified spell_file in the .tome directory
    spell_file_path = os.path.join(tome_dir, f"{spell_file}.spell")
    with open(spell_file_path, 'w') as f:
        f.write(f"# Description: {description}\n\n")
        for command in entered_commands:
            f.write(f" cast {command}\n")

    click.echo(f"Macro spell created and stored in {spell_file_path}")

@click.command()
@click.argument('spell_file', required=True)
def unseen_servant(spell_file):
    """Schedule a spell to be cast on a regular basis."""
    # Implementation of unseen_servant...

@click.command()
@click.argument('spell_file', required=True)
def enchant(spell_file):
    """Convert the file type of a file to another type."""

@click.command()
def arcane_intellect():
    """Call upon the arcane intellect of an artificial intelligence to answer your questions and generate spells or Python scripts."""
    message_log = [
        {"role": "system", "content": "You are a wizard trained in the arcane. You have deep knowledge of software development and computer science. You can cast spells and read tomes to gain knowledge about problems. Please greet the user. All code and commands should be in code blocks in order to properly help the user craft spells."}
    ]

    last_response = ""
    first_request = False

    while True:
        user_input = input("You: ")

        if user_input.lower() == "quit":
            print("I await your summons.")
            break

        elif user_input.lower() == "scribe":
            # Prompt the user whether they want to save the last response as a spell file, bash file, Python script, or just copy the last message
            save_prompt = input("Do you want to save the last response as a spell file, bash file, Python script, or just copy the last message? (spell/bash/python/copy/none): ")

            if save_prompt.lower() == "spell":
                # Save as spell file
                code_blocks = re.findall(r'(```bash|`)(.*?)(```|`)', last_response, re.DOTALL)
                code = '\n'.join(block[1].strip() for block in code_blocks)
                spell_file_name = input("Enter the name for the spell file (without the .spell extension): ")
                spell_file_path = f".tome/{spell_file_name}.spell"
                with open(spell_file_path, 'w') as f:
                    if code_blocks:
                        f.write(code)
                    else:
                        f.write(last_response)
                print(f"Spell saved as {spell_file_name}.spell in .tome directory.")

            elif save_prompt.lower() == "bash":
                # Save as bash file
                code_blocks = re.findall(r'(```bash|`)(.*?)(```|`)', last_response, re.DOTALL)
                code = '\n'.join(block[1].strip() for block in code_blocks)
                bash_file_name = input("Enter the name for the Bash script (without the .sh extension): ")
                with open(f"{bash_file_name}.sh", 'w') as f:
                    if code_blocks:
                        f.write(code)
                    else:
                        f.write(last_response)
                print(f"Bash script saved as {bash_file_name}.sh.")

            elif save_prompt.lower() == "python":
                # Save as Python script
                code_blocks = re.findall(r'(```python|`)(.*?)(```|`)', last_response, re.DOTALL)
                code = '\n'.join(block[1].strip() for block in code_blocks)
                python_file_name = input("Enter the name for the Python script (without the .py extension): ")
                with open(f"{python_file_name}.py", 'w') as f:
                    if code_blocks:
                        f.write(code)
                    else:
                        f.write(last_response)
                print(f"Python script saved as {python_file_name}.py.")

            elif save_prompt.lower() == "copy":
                # Copy the last message
                code = last_response
                message_file_name = input("Enter the name for the message file (without the .txt extension): ")
                with open(f"{message_file_name}.txt", 'w') as f:
                    f.write(code)
                print(f"Message saved as {message_file_name}.txt.")
        else:
            message_log.append({"role": "user", "content": user_input})
            response = send_message(message_log)
            message_log.append({"role": "assistant", "content": response})
            print(f"mAGI: {response}")
            last_response = response

@click.command()
@click.argument('file', required=False)
def ponder(file):
    """Ponders a specific file or all spells in the .orb directory."""
    orb_dir = ".orb"

    # If .orb directory does not exist, create it
    if not os.path.exists(orb_dir):
        os.mkdir(orb_dir)

    if file:
        # If a file argument was supplied, check if it exists in the current directory
        if os.path.exists(file):
            with open(file, 'r') as f:
                print(f.read())
        else:
            # If it doesn't exist in the current directory, check the .orb directory
            file_path = os.path.join(orb_dir, f"{file}.spell")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    print(f.read())
            else:
                print(f"File {file} does not exist in current directory or .orb directory.")
    else:
        # If no file argument was supplied, generate spell files as before
        all_spells = [member for name, member in inspect.getmembers(sys.modules[__name__]) if isinstance(member, click.core.Command)]
        for spell in all_spells:
            spell_file = os.path.join(orb_dir, f"{spell.name}.spell")
            if not os.path.exists(spell_file):
                doc = inspect.getdoc(spell)
                if doc is not None:
                    with open(spell_file, 'w') as f:
                        f.write("# " + doc.replace('\n', '\n# ') + "\n")
                        f.write("# Source code:\n")
                        f.write(click.formatting.wrap_text(spell.callback.__doc__))
                        f.write("\n")
                        f.write(click.formatting.wrap_text(inspect.getsource(spell.callback)))

        # List all the .spell files in the .orb directory
        spell_files = glob.glob(os.path.join(orb_dir, "*.spell"))
        files = [os.path.splitext(os.path.basename(f))[0] for f in spell_files]
        if files:
            click.echo("You ponder the orb. Runic glyphs expand in the vortices. Your mind fills with knowledge of the arcane:")
            for file in files:
                click.echo(file)
            spell_name_to_ponder = click.prompt("Which spell would you like to ponder?", type=str)
            spell_file_path = os.path.join(orb_dir, f"{spell_name_to_ponder}.spell")
            if os.path.exists(spell_file_path):
                with open(spell_file_path, 'r') as f:
                    click.echo(f.read())
            else:
                click.echo(f"Spell {spell_name_to_ponder} does not exist in the .orb directory.")
        else:
            click.echo("No magics were found in your orb.")

@click.command()
@click.argument('spell_file', required=True)
def exile(spell_file):
    '''Banish a spell to the /tmp directory in a .exile folder. If no /tmp directory exists, place it in a C:\temp directory.'''
    # Check if /tmp exists
    if os.path.exists("/tmp"):
        exile_dir_unix = "/tmp/.exile"
        if not os.path.exists(exile_dir_unix):
            os.mkdir(exile_dir_unix)
        shutil.move(spell_file, os.path.join(exile_dir_unix, os.path.basename(spell_file)))
        click.echo(f"Spell {spell_file} has been banished to the /tmp directory in a .exile folder.")
    else:
        exile_dir_win = "C:\\temp\\.exile"
        if not os.path.exists(exile_dir_win):
            os.mkdir(exile_dir_win)
        shutil.move(spell_file, os.path.join(exile_dir_win, os.path.basename(spell_file)))
        click.echo(f"Spell {spell_file} has been banished to the C:\\temp directory in a .exile folder.")

@click.command()
@click.argument('file_path', required=True)
def runecraft(file_path):
    '''Generate a GUI for a Bash script in the form of an enchanted rune.'''
    print("Gathering the mana...")
    print("Applying the enchantment...")
    print("Engaging the arcane energies...")
    print("Engraving the rune from aether to stone...")
    print("(This may take up to 15 seconds)")

    # Example usage
    prompt = "Rune magic, arcane symbol, runework, gemstone, central sigil, ancient arcane language, modern pixel video game style icon, engraved in the aether and onto stone, magical energy"
    generated_image = generate_image(prompt)

    # Apply circular mask
    mask = create_circular_mask(generated_image)
    circular_image = ImageOps.fit(generated_image, mask.size, centering=(0.5, 0.5))
    circular_image.putalpha(mask)

    # Get the image size to set the window size
    image_width, image_height = circular_image.size
    base_filename = os.path.basename(file_path)
    file_extension = os.path.splitext(base_filename)[1]

    # Create a new directory for the rune
    rune_dir = f".runes/{base_filename.rsplit('.', 1)[0]}"
    os.makedirs(rune_dir, exist_ok=True)

    # Save the generated image as a PNG
    image_file = base_filename.rsplit('.', 1)[0] + '_image.png'
    image_full_path = os.path.join(rune_dir, image_file)
    circular_image.save(image_full_path, format="PNG")


    # Define a dictionary that maps file extensions to commands
    extension_to_command = {
        '.sh': 'bash',
        '.py': 'python',
        '.spell': 'cast'
    }

    # Get the command for the input file's extension
    command = extension_to_command.get(file_extension, '')

    # Handle the case where the file extension is not supported
    if not command:
        print(f"File extension '{file_extension}' is not supported.")
        return

    gui_file_name = base_filename.rsplit('.', 1)[0] + '_gui.py'
    image_file = base_filename.rsplit('.', 1)[0] + '_image.png'


    # Save the generated image as a PNG in the rune directory
    circular_image.save(os.path.join(rune_dir, image_file), format="PNG")

    code = f'''
import sys
import subprocess
import signal
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QApplication, QLabel, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import Qt

# Ignore SIGINT
signal.signal(signal.SIGINT, signal.SIG_IGN)

class ImageButton(QLabel):
    def __init__(self, image_path, command, file_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pixmap = QPixmap(image_path)
        self.command = command
        self.file_path = file_path
        self.moved = False

        # Create a QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)  # Adjust the blur radius
        shadow.setXOffset(5)  # Adjust the horizontal offset
        shadow.setYOffset(5)  # Adjust the vertical offset
        shadow.setColor(QColor("black"))

        # Apply the shadow effect to the image_button
        self.setGraphicsEffect(shadow)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.moved = True
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and not self.moved:
            subprocess.run([self.command, self.file_path])
        self.moved = False
        super().mouseReleaseEvent(event)

class DraggableWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mpos = None

    def mousePressEvent(self, event):
        self.mpos = event.pos()

    def mouseMoveEvent(self, event):
        if self.mpos:
            diff = event.pos() - self.mpos
            new_pos = self.pos() + diff
            self.move(new_pos)

    def mouseReleaseEvent(self, event):
        self.mpos = None
        self.findChild(ImageButton).moved = False

app = QApplication(sys.argv)

window = DraggableWindow()
window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
window.setAttribute(Qt.WA_TranslucentBackground)

layout = QVBoxLayout(window)
layout.setAlignment(Qt.AlignCenter) # Center alignment

image_button = ImageButton(r"{image_full_path}", "{command}", "{file_path}")
layout.addWidget(image_button)

# Add a close button
close_button = QPushButton("X", window)
close_button.clicked.connect(app.quit)
close_button.setStyleSheet(\"""
    QPushButton {{
        color: teal; 
        background-color: black; 
        border-radius: 10px; 
        font-size: 12px; 
        padding: 2px;
    }}
    QPushButton:hover {{
        background-color: #ff7f7f;
    }}
\""")
# Set button size
close_button.setFixedSize(20, 20)

# Calculate the new size for the window and image by halving the current size
new_size = window.size() * 0.25

# Scale the image to the new size while maintaining aspect ratio
scaled_pixmap = image_button.pixmap.scaled(new_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

# Set the scaled pixmap as the image button's pixmap
image_button.setPixmap(scaled_pixmap)

# Resize the window to the new size
window.resize(new_size)

# Calculate the position to center the image within the window
image_pos = window.rect().center() - image_button.rect().center()
image_button.move(image_pos)

# Move the close button to the top left
close_button.move(110, 0)

window.show()

sys.exit(app.exec_())

'''

    # Write the PyQt script to a file in the rune directory
    with open(os.path.join(rune_dir, gui_file_name), 'w') as f:
        f.write(code)

    print("The rune is complete. You may now cast it.")

    # Now run the new file
    subprocess.Popen(["python", os.path.join(rune_dir, gui_file_name)], start_new_session=True)



cli.add_command(fireball)
cli.add_command(necromancy)
cli.add_command(raise_dead)
cli.add_command(divine)
cli.add_command(enchant)
cli.add_command(spellcraft)
cli.add_command(unseen_servant)
cli.add_command(ponder)
cli.add_command(arcane_intellect)
cli.add_command(exile)
cli.add_command(runecraft)

# Add commands with aliases
cli.add_command(fireball, name='fb')
cli.add_command(necromancy, name='ncr')
cli.add_command(raise_dead, name='rd')
cli.add_command(divine, name='dv')
cli.add_command(enchant, name='enc')
cli.add_command(spellcraft, name='spc')
cli.add_command(unseen_servant, name='uss')
cli.add_command(ponder, name='pn')
cli.add_command(arcane_intellect, name='ai')
cli.add_command(exile, name='ex')
cli.add_command(runecraft, name='rc')

if __name__ == "__main__":
    cast() # type: ignore