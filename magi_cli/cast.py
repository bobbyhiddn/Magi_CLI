#!/usr/bin/env python3

import click # type: ignore
import os
import sys
import glob
from magi_cli.spells import commands_list, aliases, SANCTUM_PATH
from magi_cli.loci.spellcraft.spell_parse import SpellParser  # Import SpellParser

@click.group()
@click.pass_context
def cli(ctx):
    """A Python CLI for casting spells."""
    pass

for command in commands_list:
    cli.add_command(command)

# Non-click functions

def execute_bash_file(filename):
    # Just pass through to the terminal's bash
    os.system(f"bash {filename}")

# Updated execute_python_file function to accept args
def execute_python_file(filename, args):
    # Just pass through to the terminal's python
    args_str = ' '.join(args) if args else ''
    os.system(f"{sys.executable} {filename} {args_str}")

# Click functions

@click.command()
@click.argument('input', nargs=-1)
@click.option('--verbose', '-v', count=True, help='Increase output verbosity. Use -v or -vv')
def cast(input, verbose, **kwargs):
    input = list(input)  # Convert input into a list to separate command and arguments

    # Use SANCTUM_PATH for the .tome directory
    tome_path = os.path.join(SANCTUM_PATH, '.tome')

    if not input:
        # Display available commands and spells if no input is provided
        click.echo(click.style("🎭 Available Commands:", fg="bright_blue", bold=True))
        for name, command in cli.commands.items():
            click.echo(click.style(f"  ⚡ {name}:", fg="cyan") + f" {command.help}")

        click.echo("\n" + click.style("📚 Available spells recorded in your tome:", fg="bright_blue", bold=True))
        for file in glob.glob(f"{tome_path}/*.spell"):
            click.echo(click.style(f"  🔮 {os.path.basename(file)}", fg="magenta"))
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
        spell_name = input[0]
        args = input[1:] if len(input) > 1 else []
        
        # Check if it's a direct script file
        if os.path.isfile(spell_name):
            try:
                if spell_name.endswith('.py'):
                    execute_python_file(spell_name, args)
                elif spell_name.endswith('.sh'):
                    execute_bash_file(spell_name)
                else:
                    # Try to execute as a spell
                    success = SpellParser.execute_spell_file(spell_name, *args, verbose=verbose)
                    if not success:
                        print(f"Error: Failed to execute spell '{spell_name}'.")
            except Exception as e:
                print(f"Error executing script: {e}")
                sys.exit(1)
        else:
            # Try to execute as a spell
            success = SpellParser.execute_spell_file(spell_name, *args, verbose=verbose)
            if not success:
                print(f"Error: Failed to execute spell '{spell_name}'.")

def main():
    cast()

if __name__ == "__main__":
    main()