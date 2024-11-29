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
@click.pass_context
def cli(ctx):
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

def execute_spell_file(spell_name: str) -> None:
    """
    Execute a spell file (.spell) from the .tome directory.
    
    Args:
        spell_name: Name of the spell to execute
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
                    execute_python_file(str(script_path), [])
                elif script_path.suffix == '.sh':
                    execute_bash_file(str(script_path))
                else:
                    click.echo(f"Unsupported script type: {script_path.suffix}")
            except subprocess.CalledProcessError as e:
                click.echo(f"Spell execution failed with exit code {e.returncode}")

# Click functions

@click.command()
@click.argument('input', nargs=-1)
def cast(input, **kwargs):
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
            print(f"- {os.path.basename(file)}")

    elif input[0] in aliases:
        command = aliases[input[0]]
        ctx = click.get_current_context()
        if len(input) > 1:
            ctx.invoke(command, args=input[1:])
        else:
            if 'alias' in kwargs:
                ctx.invoke(command, alias=kwargs['alias'])
            else:
                ctx.invoke(command)
    elif input[0] in cli.commands:
        ctx = click.get_current_context()
        command = cli.commands[input[0]]
        if len(input) > 1:
            # Ensure the arguments are passed correctly
            ctx.invoke(command, args=input[1:])
        else:
            if 'alias' in kwargs:
                ctx.invoke(command, alias=kwargs['alias'])
            else:
                ctx.invoke(command)

    else:
        # Check if the input is a file and execute accordingly
        file_path = os.path.join(tome_path, input[0])
        if os.path.isfile(file_path) or os.path.isfile(input[0]):
            target_file = file_path if os.path.isfile(file_path) else input[0]
            if target_file.endswith(".py"):
                execute_python_file(target_file, input[1:])
            elif target_file.endswith(".spell"):
                execute_spell_file(target_file.replace(".spell", ""))
            elif target_file.endswith(".sh"):
                execute_bash_file(target_file)
        else:
            print(f"Error: Command or file '{input[0]}' not found.")

def main():
    cast()

if __name__ == "__main__":
    main()