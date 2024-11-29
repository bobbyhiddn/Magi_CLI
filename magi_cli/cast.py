#!/usr/bin/env python3

import click # type: ignore
import subprocess
import sys
import os
import glob
import json
import zipfile
import tempfile
import shutil
import platform
from pathlib import Path
from magi_cli.spells import commands_list, aliases, SANCTUM_PATH

@click.group()
@click.pass_context
def cli(ctx):
    """A Python CLI for casting spells."""
    pass

for command in commands_list:
    cli.add_command(command)

# Non-click functions

def execute_bash_file(filename):
    """Execute bash file with platform-specific handling."""
    if platform.system() == 'Windows':
        # On Windows, try git bash first, then WSL
        try:
            git_bash = r"C:\Program Files\Git\bin\bash.exe"
            if os.path.exists(git_bash):
                subprocess.run([git_bash, filename], check=True)
            else:
                # Try WSL if git bash isn't available
                wsl_path = filename.replace('\\', '/').replace('C:', '/mnt/c')
                subprocess.run(["wsl", "bash", wsl_path], check=True)
        except subprocess.CalledProcessError as e:
            click.echo(f"Error executing bash file: {e}")
            raise
    else:
        # Unix-like systems
        subprocess.run(["bash", filename], check=True)

def execute_platform_command(command: str) -> bool:
    """Execute platform-specific commands with proper error handling."""
    try:
        if platform.system() == 'Windows':
            if command.startswith('explorer'):
                # Handle Windows explorer commands
                path = command.split(' ', 1)[1].strip()
                try:
                    import winreg
                except ImportError:
                    # Fall back to os.startfile if winreg is not available
                    os.startfile(os.path.normpath(path))
                    return True
                    
                try:
                    # Use Windows Explorer directly
                    subprocess.run(['explorer.exe', os.path.normpath(path)], check=False)
                    return True
                except subprocess.SubprocessError:
                    # Fall back to os.startfile if explorer.exe fails
                    os.startfile(os.path.normpath(path))
                    return True
            elif command.startswith('rm -rf'):
                # Convert rm -rf to Windows equivalent
                path = command.split(' ', 2)[2].strip()
                if os.path.exists(path):
                    shutil.rmtree(path, ignore_errors=True)
                return True
            elif command.startswith('mkdir'):
                # Handle mkdir with -p equivalent behavior
                path = command.split(' ', 1)[1].strip()
                os.makedirs(path, exist_ok=True)
                return True
            elif command.startswith('mv'):
                # Handle move command with pattern support
                parts = command.split(' ')
                if len(parts) >= 3:
                    pattern = parts[1]
                    dest = ' '.join(parts[2:])  # Handle destinations with spaces
                    matched_files = glob.glob(pattern)
                    if not matched_files:
                        click.echo(f"Warning: No files matched pattern '{pattern}'")
                        return False
                    for file in matched_files:
                        try:
                            shutil.move(file, dest)
                        except (shutil.Error, OSError) as e:
                            click.echo(f"Warning: Could not move '{file}': {e}")
                            return False
                    return True
                return False
        
        # For all other commands or non-Windows systems
        result = subprocess.run(command, shell=True, check=False)
        if result.returncode != 0:
            click.echo(f"Warning: Command '{command}' returned non-zero exit code {result.returncode}")
            return False
        return True
    except Exception as e:
        click.echo(f"Warning: Command '{command}' failed: {str(e)}")
        return False

def execute_python_file(filename, args):
    """Execute Python file with better error handling."""
    try:
        subprocess.run([sys.executable, filename, *args], check=True)
    except subprocess.CalledProcessError as e:
        # Suppress the error stacktrace but show a user-friendly message
        click.echo(f"Warning: Script execution failed with exit code {e.returncode}")
        return False
    return True

def extract_spell_bundle(spell_path: Path) -> tuple[Path, dict]:
    """Extracts a spell bundle to a temporary directory and returns the path and metadata."""
    temp_dir = Path(tempfile.mkdtemp(prefix='magi_spell_'))
    
    with zipfile.ZipFile(spell_path, 'r') as spell_zip:
        spell_zip.extractall(temp_dir)
    
    metadata_path = temp_dir / 'spell.json'
    if not metadata_path.exists():
        shutil.rmtree(temp_dir)
        raise ValueError(f"Invalid spell bundle: missing metadata file")
    
    metadata = json.loads(metadata_path.read_text())
    return temp_dir, metadata

def execute_spell_file(spell_file, args=None):
    """Execute a spell file with optional arguments."""
    if args is None:
        args = []
    
    tome_path = os.path.join(SANCTUM_PATH, '.tome')
    spell_file_path = spell_file if '.tome' in spell_file else os.path.join(tome_path, spell_file)

    if not spell_file_path.endswith('.spell'):
        spell_file_path += '.spell'
    
    if not os.path.exists(spell_file_path):
        click.echo(f"Could not find {spell_file}.spell in .tome directory. Checking current directory for .tome directory...")
        spell_file_path = os.path.join(".tome", spell_file)
        if not os.path.exists(spell_file_path):
            click.echo(f"Could not find {spell_file}.spell in current directory or .tome directory.")
            return
        elif not spell_file_path.endswith('.spell'):
            spell_file_path += '.spell'

    try:
        # Try to extract as a bundled spell
        temp_dir, metadata = extract_spell_bundle(Path(spell_file_path))
        try:
            main_script = temp_dir / metadata['main_script']
            success = False
            if main_script.suffix == '.py':
                success = execute_python_file(str(main_script), args)
            elif main_script.suffix == '.sh':
                success = execute_bash_file(str(main_script))
            
            if not success:
                click.echo("Note: Spell completed with some warnings.")
        finally:
            shutil.rmtree(temp_dir)
    except (zipfile.BadZipFile, KeyError):
        # Fall back to legacy spell file format
        with open(spell_file_path, 'r') as file:
            lines = file.readlines()
        
        all_succeeded = True
        for line in lines:
            stripped_line = line.strip()
            if stripped_line and not stripped_line.startswith("#"):
                if not execute_platform_command(stripped_line):
                    all_succeeded = False
        
        if not all_succeeded:
            click.echo("Note: Some commands completed with warnings.")

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
            args = input[1:] if len(input) > 1 else []
            
            if target_file.endswith(".py"):
                execute_python_file(target_file, args)
            elif target_file.endswith(".spell"):
                execute_spell_file(target_file.replace(".spell", ""), args)
            elif target_file.endswith(".sh"):
                execute_bash_file(target_file)
        else:
            print(f"Error: Command or file '{input[0]}' not found.")

def main():
    cast()

if __name__ == "__main__":
    main()