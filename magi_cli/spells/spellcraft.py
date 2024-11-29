import click
import os
import json
import zipfile
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from magi_cli.spells import SANCTUM_PATH

def create_spell_bundle_from_directory(spell_dir: str, spell_name: str, description: str) -> str:
    """Creates a spell bundle (.spell ZIP file) from a directory containing the spell scripts and templates."""
    tome_dir = Path(SANCTUM_PATH) / '.tome'
    tome_dir.mkdir(parents=True, exist_ok=True)

    spell_filename = f"{spell_name}.spell"
    spell_path = tome_dir / spell_filename

    # Create a temporary directory to hold spell contents
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Copy all contents from the spell directory to temp directory
        for item in os.listdir(spell_dir):
            s = os.path.join(spell_dir, item)
            d = os.path.join(temp_path, item)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

        # Determine the main script (the script with the same base name as the spell)
        main_script = None
        for ext in ['.py', '.sh']:
            possible_script = os.path.join(temp_path, spell_name + ext)
            if os.path.isfile(possible_script):
                main_script = spell_name + ext
                break

        if not main_script:
            # If no script with the spell name is found, pick the first script file
            script_files = [f for f in os.listdir(temp_path) if f.endswith(('.py', '.sh'))]
            if len(script_files) == 1:
                main_script = script_files[0]
            elif len(script_files) > 1:
                click.echo("Multiple script files detected:")
                for idx, fname in enumerate(script_files, start=1):
                    click.echo(f"{idx}. {fname}")
                choice = click.prompt("Select the main script by number", type=int)
                main_script = script_files[choice - 1]
            else:
                click.echo(f"No script files found in '{spell_dir}'.")
                return ''

        # Create metadata
        metadata = {
            'name': spell_name,
            'description': description,
            'created_at': datetime.utcnow().isoformat(),
            'main_script': main_script
        }
        metadata_path = temp_path / 'spell.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        # Create the .spell ZIP file
        with zipfile.ZipFile(spell_path, 'w', zipfile.ZIP_DEFLATED) as spell_zip:
            for root, dirs, files in os.walk(temp_path):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(temp_path)
                    spell_zip.write(file_path, arcname)

    return str(spell_path)

@click.command()
@click.argument('spell_dir', required=False)
def spellcraft(spell_dir=None):
    """ 'sc' - Weaves a macro spell out of scripts and stores it in ~/.sanctum/.tome.
    Usage: cast sc <spell_directory> """
    if not spell_dir:
        click.echo("Usage: cast sc <spell_directory>")
        return

    tome_dir = os.path.join(SANCTUM_PATH, '.tome')
    os.makedirs(tome_dir, exist_ok=True)

    if not os.path.isdir(spell_dir):
        click.echo(f"Provided path '{spell_dir}' is not a directory.")
        return

    spell_name = os.path.basename(spell_dir.rstrip('/\\'))
    if spell_name.endswith('.spell'):
        spell_name = spell_name[:-6]

    description = click.prompt("Enter a description for the spell")

    # Create the spell bundle
    bundle_path = create_spell_bundle_from_directory(spell_dir, spell_name, description)
    if bundle_path:
        click.echo(f"Spell '{spell_name}' created and stored at: {bundle_path}")

alias = "sc"

def main():
    spellcraft()

if __name__ == '__main__':
    main()
