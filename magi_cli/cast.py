#!/usr/bin/env python3

import click # type: ignore
import subprocess
import sys
import os
import shutil
import inspect
import re
import shutil
import tempfile
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
from git import Repo # type: ignore
from flask import Flask, render_template_string, request # type: ignore
from magi_cli.spells import commands_list

# Load the Openai API key
# This can also be done by setting the OPENAI_API_KEY environment variable manually.
# load_dotenv() # Uncomment this line if you want to load the API key from the .env file
api_key = os.getenv("OPENAI_API_KEY")

# Load the defauit .tome directory path
tome_path = os.getenv("TOME_PATH")

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
    tome_path = os.getenv("TOME_PATH")  # Get default .tome location from environment variable
    spell_file_path = spell_file if '.tome' in spell_file else os.path.join(tome_path, spell_file)

    # Check if spell file has .spell extension, add if missing
    if not spell_file_path.endswith('.spell'):
        spell_file_path += '.spell'
    
    # Check if the spell_file exists in the tome_path
    if not os.path.exists(spell_file_path):
        click.echo(f"Could not find {spell_file}.spell in .tome directory. Checking current directory for .tome directory...")
        spell_file_path = os.path.join(".tome", spell_file)
        if not os.path.exists(spell_file_path):
            click.echo(f"Could not find {spell_file}.spell in current directory or .tome directory.")
            return
        elif not spell_file_path.endswith('.spell'):
            spell_file_path += '.spell'

    with open(spell_file_path, 'r') as file:
        lines = file.readlines()

    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith("#"):  # Ignore comments
            continue
        subprocess.run(stripped_line, shell=True)

# Click functions

@click.command()
@click.argument('input', nargs=-1)
def cast(input):
    input = " ".join(input)  # join input arguments into one string if there are multiple

    # Get the tome_path, use the current directory's .tome if TOME_PATH is not set
    tome_path = os.getenv("TOME_PATH", ".tome")

    file_path = os.path.join(tome_path, input)

    # If no input is provided, list all available commands and .spell files
    if not input:
        # Print all available commands
        print("Available commands:")
        for name, command in cli.commands.items(): # type: ignore
            print(f"- {name}: {command.help}")

        # Print all .spell files in TOME_PATH
        print("\nAvailable spells recorded in your tome:")
        for file in glob.glob(f"{tome_path}/*.spell"):
            print(f"- {os.path.basename(file)}")

    elif input in cli.commands:  # Check if input matches a registered command
        cli()  # Invoke the matched command directly # type: ignore
    elif os.path.isfile(file_path) or os.path.isfile(input):  # Check if file exists in TOME_PATH or directly
        target_file = file_path if os.path.isfile(file_path) else input  # Use the file that exists
        if target_file.endswith(".py"):  # If it's a Python script
            execute_python_file(target_file)  # execute the Python script
        elif target_file.endswith(".spell"):  # If it's a spell file
            execute_spell_file(target_file.replace(".spell", ""))  # execute the spell
        elif target_file.endswith(".sh"):  # If it's a bash file
            execute_bash_file(target_file)  # execute the bash file
        else:  # if it's not a Python script or a spell file
            cli()  # type: ignore
    else:
        cli()  # type: ignore

@click.group()
@click.pass_context
def cli(ctx):
    """A Python CLI for casting spells."""
    pass

for command in commands_list:
    cli.add_command(command)


if __name__ == "__main__":
    cast() # type: ignore