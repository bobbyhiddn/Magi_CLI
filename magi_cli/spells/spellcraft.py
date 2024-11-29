import click
import os
import json
import zipfile
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from magi_cli.spells import SANCTUM_PATH

def create_spell_bundle_from_directory(spell_dir: Path, spell_name: str, description: str) -> Path:
    """Creates a spell bundle (.spell ZIP file) from a directory containing the spell scripts and templates."""
    tome_dir = Path(SANCTUM_PATH) / '.tome'
    tome_dir.mkdir(parents=True, exist_ok=True)

    spell_path = tome_dir / f"{spell_name}.spell"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Copy contents
        shutil.copytree(spell_dir, temp_path, dirs_exist_ok=True)

        # Find main script
        main_script = None
        # First try exact name match
        for ext in ['.py', '.sh']:
            possible_script = temp_path / f"{spell_name}{ext}"
            if possible_script.is_file():
                main_script = f"{spell_name}{ext}"
                break

        # If no exact match, look for alternatives
        if not main_script:
            script_files = list(temp_path.glob("*.py")) + list(temp_path.glob("*.sh"))
            if len(script_files) == 1:
                main_script = script_files[0].name
            elif len(script_files) > 1:
                click.echo("Multiple script files detected:")
                for idx, fname in enumerate(script_files, start=1):
                    click.echo(f"{idx}. {fname.name}")
                choice = click.prompt("Select the main script by number", type=int)
                main_script = script_files[choice - 1].name
            else:
                click.echo(f"No script files found in '{spell_dir}'")
                return None

        # Create metadata
        metadata = {
            'name': spell_name,
            'description': description,
            'created_at': datetime.utcnow().isoformat(),
            'main_script': main_script
        }
        
        metadata_path = temp_path / 'spell.json'
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')

        # Create spell bundle
        with zipfile.ZipFile(spell_path, 'w', zipfile.ZIP_DEFLATED) as spell_zip:
            for file_path in temp_path.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(temp_path)
                    spell_zip.write(file_path, arcname)

    return spell_path

@click.command()
@click.argument('args', nargs=-1)
def spellcraft(args):
    """'sc' - Weaves a macro spell out of scripts and stores it in ~/.sanctum/.tome."""
    if not args:
        click.echo("Error: Please provide a directory path.")
        return
    
    spell_dir = Path(args[0])
    if not spell_dir.is_dir():
        click.echo(f"Error: '{spell_dir}' is not a directory.")
        return

    spell_name = spell_dir.name.removesuffix('.spell')
    description = click.prompt("Enter a description for the spell")

    bundle_path = create_spell_bundle_from_directory(spell_dir, spell_name, description)
    if bundle_path:
        click.echo(f"Success: Spell '{spell_name}' created at: {bundle_path}")

alias = "sc"

if __name__ == '__main__':
    spellcraft()
