#!/usr/bin/env python3

import click # type: ignore
import subprocess
import sys
import os
import shutil
import inspect
import re
from datetime import datetime
import glob
from pathlib import Path
from click import Context # type: ignore
import openai
from dotenv import load_dotenv

# Load the API key from the .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Set the API key for the OpenAI package through .env file or API key path
# You can also set it by using export OPENAI_API_KEY=<your-api-key> in the terminal.
openai.api_key = api_key
# openai.api_key_path = ".api"

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
@click.argument('path', required=False)
def divine(path):
    """List the directory contents with detailed information."""
    if not path:
        path = os.getcwd()  # Set the current directory if no path is specified

    if os.path.exists(path):
        click.echo(f"You cast your senses into the ether, seeking knowledge of the realm at {path}...\n")
        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            file_size = os.path.getsize(file_path)
            file_permissions = oct(os.stat(file_path).st_mode)[-3:]
            file_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
            click.echo(f"{file}\tSize: {file_size} bytes\tPermissions: {file_permissions}\tLast Modified: {file_modified}")
    else:
        click.echo(f"Your divine senses find nothing at {path}. It seems to be a realm yet unformed.")

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

import re
import click

@click.command()
def arcane_intellect():
    """Call upon the arcane intellect of an artificial intelligence to answer your questions and generate spells or Python scripts."""
    message_log = [
        {"role": "system", "content": "You are a wizard trained in the arcane. You have deep knowledge of software development and computer science. You can cast spells and read tomes to gain knowledge about problems. You are helping another wizard by producing spells and functions for them to use."}
    ]

    last_response = ""
    first_request = True

    while True:
        user_input = input("You: ")

        if user_input.lower() == "quit":
            print("I await your summons.")
            break

        elif user_input.lower() == "scribe":
            # Prompt the user whether they want to save the last response as a spell file or a Python script
            save_prompt = input("Do you want to save the last response as a spell file or a Python script? (spell/python/none): ")

            # Extract code blocks from the last response
            code_blocks = re.findall(r'(```python|`)(.*?)(```|`)', last_response, re.DOTALL)
            code = '\n'.join(block[1].strip() for block in code_blocks)

            if save_prompt.lower() == "spell":
                tome_dir = ".tome"
                # os.mkdir(tome_dir)
                spell_file_name = input("Enter the name for the spell file (without the .spell extension): ")
                with open(f".tome/{spell_file_name}.spell", 'w') as f:
                    f.write(code)
                print(f"Spell saved as {spell_file_name}.spell in .tome directory.")
            elif save_prompt.lower() == "python":
                python_file_name = input("Enter the name for the Python script (without the .py extension): ")
                with open(f"{python_file_name}.py", 'w') as f:
                    f.write(code)
                print(f"Python script saved as {python_file_name}.py.")
        else:
            if not first_request:
                message_log.append({"role": "user", "content": user_input})
            response = send_message(message_log)
            message_log.append({"role": "assistant", "content": response})
            print(f"mAGI: {response}")
            last_response = response
            first_request = False

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



cli.add_command(fireball)
cli.add_command(necromancy)
cli.add_command(raise_dead)
cli.add_command(divine)
cli.add_command(enchant)
cli.add_command(spellcraft)
cli.add_command(unseen_servant)
cli.add_command(ponder)
cli.add_command(arcane_intellect)

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

if __name__ == "__main__":
    cast() # type: ignore