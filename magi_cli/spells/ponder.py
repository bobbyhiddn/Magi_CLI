import click
import inspect
import os
import sys
import glob
import requests
from typing import Optional, Dict, Any
from magi_cli.spells import SANCTUM_PATH

class SpellRegistry:
    def __init__(self, chamber_url: str = "https://magi-chamber.fly.dev"):
        self.chamber_url = chamber_url.rstrip('/')
        self.orb_dir = os.path.join(SANCTUM_PATH, '.orb')
        os.makedirs(self.orb_dir, exist_ok=True)

    def fetch_spell_manifest(self) -> Optional[Dict[str, Any]]:
        """Fetch the spell manifest from the chamber."""
        try:
            response = requests.get(f"{self.chamber_url}/manifest")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            click.echo(f"Failed to contact the chamber: {e}")
            return None

    def fetch_spell(self, spell_name: str) -> Optional[str]:
        """Fetch a specific spell from the chamber."""
        try:
            response = requests.get(f"{self.chamber_url}/spells/{spell_name}")
            response.raise_for_status()
            return response.text
        except requests.RequestException:
            return None

    def sync_spells(self) -> None:
        """Synchronize local spell cache with chamber."""
        manifest = self.fetch_spell_manifest()
        if not manifest:
            click.echo("Failed to fetch spell manifest from the chamber.")
            return

        for spell_name, spell_info in manifest.get("spells", {}).items():
            local_path = os.path.join(self.orb_dir, f"{spell_name}.spell")
            
            # Check if we need to update the spell
            needs_update = True
            if os.path.exists(local_path):
                with open(local_path, 'r') as f:
                    local_content = f.read()
                    if spell_info.get("hash") == self._calculate_hash(local_content):
                        needs_update = False

            if needs_update:
                spell_content = self.fetch_spell(spell_name)
                if spell_content:
                    with open(local_path, 'w') as f:
                        f.write(spell_content)
                    click.echo(f"Updated spell: {spell_name}")

    def _calculate_hash(self, content: str) -> str:
        """Calculate hash of spell content for comparison."""
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()

    def list_spells(self) -> None:
        """List all available spells with their descriptions."""
        try:
            # Fetch from chamber
            response = requests.get(f"{self.chamber_url}/spells")
            response.raise_for_status()
            remote_spells = response.json()
            
            click.echo("\n=== Remote Spells ===")
            for spell in remote_spells.get("spells", []):
                if spell and 'name' in spell:
                    formatted_desc = spell.get('formatted_description', f"{spell['name']} - {spell.get('description', 'No description')}")
                    click.echo(formatted_desc)

            # List local spells
            click.echo("\n=== Local Spells ===")
            spell_files = glob.glob(os.path.join(self.orb_dir, "*.spell"))
            for spell_path in spell_files:
                spell_name = os.path.splitext(os.path.basename(spell_path))[0]
                with open(spell_path, 'r') as f:
                    first_line = f.readline().strip()
                    desc = first_line if first_line.startswith('#') else "No description"
                    click.echo(f"{spell_name}: {desc}")

        except requests.RequestException as e:
            click.echo(f"Failed to fetch remote spells: {e}")
            # Still show local spells if remote fails
            spell_files = glob.glob(os.path.join(self.orb_dir, "*.spell"))
            for spell_path in spell_files:
                spell_name = os.path.splitext(os.path.basename(spell_path))[0]
                click.echo(spell_name)

@click.command()
@click.argument('args', nargs=-1, required=False)
def ponder(args):
    """'pd' - Ponder your .orb and the chamber to gain insight into available spells."""
    registry = SpellRegistry()
    
    if not args:
        # Interactive mode
        click.echo("You ponder the orb and gaze into the distant chamber...")
        registry.list_spells()
        
        spell_name = click.prompt("\nWhich spell would you like to ponder? (or 'sync' to synchronize with chamber)", type=str)
        
        if spell_name.lower() == 'sync':
            click.echo("Synchronizing with the chamber...")
            registry.sync_spells()
            return

        # Try local first, then remote
        local_path = os.path.join(registry.orb_dir, f"{spell_name}.spell")
        if os.path.exists(local_path):
            with open(local_path, 'r') as f:
                click.echo(f.read())
        else:
            spell_content = registry.fetch_spell(spell_name)
            if spell_content:
                click.echo(spell_content)
                save = click.confirm("Would you like to save this spell to your orb?", default=True)
                if save:
                    with open(local_path, 'w') as f:
                        f.write(spell_content)
                    click.echo(f"Spell saved to {local_path}")
            else:
                click.echo(f"Spell '{spell_name}' not found in local orb or remote chamber.")
    
    else:
        # Direct file mode
        file_name = args[0]
        local_path = os.path.join(registry.orb_dir, f"{file_name}.spell")
        
        if os.path.exists(file_name):
            with open(file_name, 'r') as f:
                click.echo(f.read())
        elif os.path.exists(local_path):
            with open(local_path, 'r') as f:
                click.echo(f.read())
        else:
            spell_content = registry.fetch_spell(file_name)
            if spell_content:
                click.echo(spell_content)
                save = click.confirm("Would you like to save this spell to your orb?", default=True)
                if save:
                    with open(local_path, 'w') as f:
                        f.write(spell_content)
                    click.echo(f"Spell saved to {local_path}")
            else:
                click.echo(f"File or spell '{file_name}' not found.")

alias = "pd"

def main():
    ponder()

if __name__ == '__main__':
    main()