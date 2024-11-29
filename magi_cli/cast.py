#!/usr/bin/env python3

import click
import subprocess
import sys
import os
import glob
import json
import zipfile
import tempfile
from pathlib import Path
from magi_cli.spells import commands_list, aliases, SANCTUM_PATH

@click.group()
def cli():
    """A Python CLI for casting spells."""
    pass

for command in commands_list:
    cli.add_command(command)

def execute_bash_file(filename: str) -> None:
    """Execute a bash script file."""
    subprocess.run(["bash", filename], check=True)

def execute_python_file(filename: str, args: list) -> None:
    """Execute a Python script file with optional arguments."""
    subprocess.run([sys.executable, filename, *args], check=True)

def execute_spell_file(spell_name: str, spell_args: list) -> None:
    """
    Execute a spell file (.spell) from the .tome directory.

    Args:
        spell_name: Name of the spell to execute
        spell_args: Arguments to pass to the spell
    """
    tome_path = Path(SANCTUM_PATH) / '.tome'
    spell_file_path = tome_path / f"{spell_name.removesuffix('.spell')}.spell"

    if not spell_file_path.exists():
        click.echo(f"Could not find {spell_name}.spell in .tome directory.")
        return

    with zipfile.ZipFile(spell_file_path, 'r') as spell_zip:
        # Extract and validate metadata
        try:
            with spell_zip.open('spell.json') as f:
                metadata = json.load(f)
        except KeyError:
            click.echo("Invalid spell file: Missing 'spell.json'")
            return

        main_script = metadata.get('main_script')
        if not main_script:
            click.echo("Invalid spell file: 'main_script' not specified in 'spell.json'")
            return

        # Execute in temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            spell_zip.extractall(temp_dir)
            script_path = Path(temp_dir) / main_script

            if not script_path.is_file():
                click.echo(f"Main script '{main_script}' not found in the spell bundle.")
                return

            # Set executable permissions
            script_path.chmod(0o775)

            # Execute based on script type
            try:
                if script_path.suffix == '.py':
                    execute_python_file(str(script_path), spell_args)
                elif script_path.suffix == '.sh':
                    execute_bash_file(str(script_path))
                else:
                    click.echo(f"Unsupported script type: {script_path.suffix}")
            except subprocess.CalledProcessError as e:
                click.echo(f"Spell execution failed with exit code {e.returncode}")

# Click functions

@click.command()
@click.argument('input', nargs=-1)
def cast(input):
    input = list(input)  # Convert input into a list to separate command and arguments

    # Use SANCTUM_PATH for the .tome directory
    tome_path = os.path.join(SANCTUM_PATH, '.tome')

    if not input:
        # Display available commands and spells if no input is provided
        print("Available commands:")
        for name, command in cli.commands.items():
            print(f"- {name}: {command.help}")

        print("\nAvailable spells recorded in your tome:")
        for file in glob.glob(f"{tome_path}/*.spell"):
            print(f"- {os.path.basename(file)[:-6]}")  # Remove '.spell' extension

    else:
        cmd_name = input[0]
        cmd_args = input[1:]

        if cmd_name in aliases:
            command = aliases[cmd_name]
            ctx = click.get_current_context()
            ctx.invoke(command, *cmd_args)
        elif cmd_name in cli.commands:
            command = cli.commands[cmd_name]
            ctx = click.get_current_context()
            ctx.invoke(command, *cmd_args)
        else:
            # Check if the input is a spell file and execute accordingly
            spell_name = cmd_name
            spell_args = cmd_args
            spell_file_path = os.path.join(tome_path, f"{spell_name}.spell")
            if os.path.isfile(spell_file_path):
                execute_spell_file(spell_name, spell_args)
            else:
                print(f"Error: Command or spell '{cmd_name}' not found.")

def main():
    cast()

if __name__ == "__main__":
    main()
