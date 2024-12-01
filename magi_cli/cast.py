#!/usr/bin/env python3

import click # type: ignore
import subprocess
import sys
import os
import glob
from magi_cli.spells import commands_list, aliases, SANCTUM_PATH
from magi_cli.modules.spell_parse import SpellParser  # Import SpellParser

@click.group()
@click.pass_context
def cli(ctx):
    """A Python CLI for casting spells."""
    pass

for command in commands_list:
    cli.add_command(command)

# Non-click functions

def execute_bash_file(filename):
    subprocess.run(["bash", filename], check=True)

# Updated execute_python_file function to accept args
def execute_python_file(filename, args):
    subprocess.run([sys.executable, filename, *args], check=True)

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
        # Use SpellParser to execute the spell file
        spell_name = input[0]
        args = input[1:] if len(input) > 1 else []
        success = SpellParser.execute_spell_file(spell_name, args)
        if not success:
            print(f"Error: Failed to execute spell '{spell_name}'.")

def main():
    cast()

if __name__ == "__main__":
    main()