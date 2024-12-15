#!/usr/bin/env python3

import click
import inspect
import os
import sys
import glob
import requests
import subprocess
import ast
import hashlib
from typing import Optional, Dict, Any, Tuple, List
from magi_cli.spells import SANCTUM_PATH
from pathlib import Path

class SpellRegistry:
    def __init__(self, chamber_url: str = "https://magi-chamber.fly.dev"):
        self.chamber_url = chamber_url.rstrip('/')
        self.orb_dir = os.path.join(SANCTUM_PATH, '.orb')
        # Get the magi_cli spells directory
        self.spells_dir = self._get_spells_dir()
        os.makedirs(self.orb_dir, exist_ok=True)
        os.makedirs(self.spells_dir, exist_ok=True)

    def _get_spells_dir(self) -> str:
        """Get the spells directory from the magi_cli package."""
        try:
            from magi_cli import spells
            spells_dir = os.path.dirname(inspect.getfile(spells))
            return spells_dir
        except ImportError:
            click.echo("Warning: Could not find magi_cli spells directory")
            return os.path.join(os.getcwd(), 'spells')

    def fetch_spell_manifest(self) -> Optional[Dict[str, Any]]:
        """Fetch the spell manifest from the chamber."""
        try:
            response = requests.get(f"{self.chamber_url}/manifest")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            click.echo(f"Failed to contact the chamber: {e}")
            return None

    def fetch_spell(self, spell_name: str) -> Optional[Tuple[str, str, List[str]]]:
        """
        Fetch a specific spell from the chamber.
        Returns tuple of (content, hash, requirements) if successful, None if failed.
        """
        try:
            response = requests.get(f"{self.chamber_url}/spells/{spell_name}.py")
            response.raise_for_status()
            content = response.text

            # Get hash from manifest
            manifest = self.fetch_spell_manifest()
            if manifest and spell_name in manifest.get("spells", {}):
                spell_hash = manifest["spells"][spell_name]["hash"]
            else:
                spell_hash = hashlib.sha256(content.encode()).hexdigest()

            # Extract requirements from the spell content
            requirements = self.extract_requirements(content)

            return content, spell_hash, requirements
        except requests.RequestException as e:
            click.echo(f"Failed to fetch spell {spell_name}: {e}")
            return None

    def extract_requirements(self, spell_script_content: str) -> List[str]:
        """Extract the __requires__ variable from the spell script content."""
        try:
            node = ast.parse(spell_script_content)
        except SyntaxError as e:
            click.echo(f"Syntax error in the spell script: {e}")
            return []

        requirements = []

        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == '__requires__':
                        if isinstance(stmt.value, (ast.List, ast.Tuple)):
                            requirements = [ast.literal_eval(elt) for elt in stmt.value.elts]
                            return requirements
                        elif isinstance(stmt.value, ast.Str):
                            requirements = [stmt.value.s]
                            return requirements
                        else:
                            click.echo("Invalid format for __requires__ in the spell script.")
                            return []
        return []

    def install_requirements(self, requirements: List[str]) -> bool:
        """Install the required dependencies for the spell."""
        try:
            click.echo(f"Installing spell dependencies: {requirements}")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', *requirements])
            return True
        except subprocess.CalledProcessError as e:
            click.echo(f"Failed to install dependencies: {e}")
            return False

    def install_spell(self, spell_name: str, content: str, requirements: List[str]) -> bool:
        """Install a spell directly to magi_cli's spells directory and update RECORD."""
        try:
            # Install dependencies if any
            if requirements:
                click.echo(f"\nSpell '{spell_name}' requires the following packages: {requirements}")
                consent = click.prompt("Do you want to proceed with installing these dependencies? (y/n)", default='y')
                if consent.lower() != 'y':
                    click.echo("Aborting spell installation.")
                    return False
                if not self.install_requirements(requirements):
                    click.echo("Failed to install spell dependencies. Aborting spell installation.")
                    return False

            # Save to spells directory
            spell_path = os.path.join(self.spells_dir, f"{spell_name}.py")
            with open(spell_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Add empty __init__.py if it doesn't exist
            init_path = os.path.join(self.spells_dir, "__init__.py")
            if not os.path.exists(init_path):
                Path(init_path).touch()

            # Find and update RECORD file
            site_packages = os.path.dirname(os.path.dirname(self.spells_dir))
            dist_info_pattern = os.path.join(site_packages, "magi_cli_pypi-*.dist-info")
            dist_info_dirs = glob.glob(dist_info_pattern)

            if dist_info_dirs:
                record_path = os.path.join(dist_info_dirs[0], "RECORD")
                if os.path.exists(record_path):
                    try:
                        with open(record_path, 'r', encoding='utf-8') as f:
                            records = f.readlines()

                        # Add new spell record if not already present
                        relative_path = "magi_cli/spells/" + f"{spell_name}.py"
                        if not any(relative_path in record for record in records):
                            records.append(f"{relative_path},,\n")

                        with open(record_path, 'w', encoding='utf-8') as f:
                            f.writelines(records)
                    except Exception as e:
                        click.echo(f"Warning: Failed to update RECORD file: {e}")

            # Try to import the spell to verify installation
            try:
                import importlib
                importlib.import_module(f"magi_cli.spells.{spell_name}")
                importlib.reload(importlib.import_module("magi_cli.spells"))
            except Exception as e:
                click.echo(f"Warning: Spell installed but import verification failed: {e}")

            click.echo(f"\nThe arcane knowledge flows into your mind...")
            click.echo(f"You have learned the '{spell_name}' spell!")
            click.echo(f"Cast it with: cast {spell_name}")
            return True
        except Exception as e:
            click.echo(f"The knowledge slips through your grasp: {e}")
            return False

    def uninstall_spell(self, spell_name: str) -> bool:
        """Uninstall a spell by removing it from spells directory and orb, and updating RECORD."""
        try:
            # Remove from spells directory
            spell_path = os.path.join(self.spells_dir, f"{spell_name}.py")
            if os.path.exists(spell_path):
                os.remove(spell_path)

            # Remove from orb directory
            orb_path = os.path.join(self.orb_dir, f"{spell_name}.spell")
            if os.path.exists(orb_path):
                os.remove(orb_path)

            # Update RECORD file
            site_packages = os.path.dirname(os.path.dirname(self.spells_dir))
            dist_info_pattern = os.path.join(site_packages, "magi_cli_pypi-*.dist-info")
            dist_info_dirs = glob.glob(dist_info_pattern)

            if dist_info_dirs:
                record_path = os.path.join(dist_info_dirs[0], "RECORD")
                if os.path.exists(record_path):
                    # Read existing records
                    with open(record_path, 'r') as f:
                        records = f.readlines()

                    # Remove spell record
                    relative_path = os.path.join("magi_cli", "spells", f"{spell_name}.py")
                    records = [record for record in records if not record.startswith(relative_path)]

                    # Write updated records
                    with open(record_path, 'w') as f:
                        f.writelines(records)

            click.echo(f"\nThe knowledge of '{spell_name}' fades from your mind...")
            click.echo(f"You have unlearned the '{spell_name}' spell.")
            return True
        except Exception as e:
            click.echo(f"Failed to unlearn '{spell_name}': {e}")
            return False

    def save_to_orb(self, spell_name: str, content: str, description: str = "") -> bool:
        """Save a spell to the orb for future reference, including its description."""
        try:
            orb_path = os.path.join(self.orb_dir, f"{spell_name}.spell")
            with open(orb_path, 'w', encoding='utf-8') as f:
                if description:
                    f.write(f"# {description}\n")
                f.write(content)
            click.echo(f"The essence of {spell_name} resonates within your orb...")
            return True
        except Exception as e:
            click.echo(f"The spell resists being bound to your orb: {e}")
            return False

    def sync_spells(self) -> None:
        """Synchronize local spell cache with chamber."""
        manifest = self.fetch_spell_manifest()
        if not manifest:
            click.echo("The chamber remains silent. No connection could be established.")
            return

        spells = manifest.get("spells", {})
        spells_synced = 0
        spells_current = 0
        spells_failed = 0

        click.echo("\nAttuning to the distant chamber's energies...")

        for spell_name, spell_info in spells.items():
            local_path = os.path.join(self.orb_dir, f"{spell_name}.spell")
            remote_hash = spell_info.get("hash")

            # Check if we need to update the spell
            needs_update = True
            if os.path.exists(local_path):
                with open(local_path, 'r') as f:
                    local_content = f.read()
                    if remote_hash == self._calculate_hash(local_content):
                        needs_update = False
                        spells_current += 1

            if needs_update:
                result = self.fetch_spell(spell_name)
                if result:
                    content, _, _ = result
                    # Save to orb
                    with open(local_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    spells_synced += 1
                    click.echo(f"The essence of {spell_name} flows into your orb...")
                else:
                    spells_failed += 1
                    click.echo(f"Failed to grasp {spell_name}...")

        # Report results
        if spells_synced == 0 and spells_failed == 0:
            click.echo(f"\nYour orb pulses with familiar energy. All {spells_current} spells are in harmony.")
        else:
            status = []
            if spells_synced > 0:
                status.append(f"{spells_synced} new mysteries captured")
            if spells_current > 0:
                status.append(f"{spells_current} spells remain in balance")
            if spells_failed > 0:
                status.append(f"{spells_failed} magics eluded your grasp")
            click.echo("\nThe synchronization ritual is complete: " + ", ".join(status))

    def relearn_spells(self) -> None:
        """Reinstall spells from orb that are missing in spells directory."""
        orb_spells = glob.glob(os.path.join(self.orb_dir, "*.spell"))
        missing_spells = []
        for orb_spell_path in orb_spells:
            spell_name = os.path.splitext(os.path.basename(orb_spell_path))[0]
            spell_path = os.path.join(self.spells_dir, f"{spell_name}.py")
            if not os.path.exists(spell_path):
                missing_spells.append(spell_name)

        if missing_spells:
            click.echo("\nYour orb holds spells that are not currently mastered:")
            for spell_name in missing_spells:
                click.echo(f"- {spell_name}")
            if click.confirm("Would you like to relearn them from the chamber?"):
                for spell_name in missing_spells:
                    result = self.fetch_spell(spell_name)
                    if result:
                        content, _, requirements = result
                        self.install_spell(spell_name, content, requirements)
                    else:
                        click.echo(f"Failed to relearn '{spell_name}'.")
            else:
                click.echo("You choose to leave the spells dormant within your orb.")
        else:
            click.echo("All spells within your orb are already mastered.")

    def list_spells(self) -> None:
        """List all available spells with their descriptions."""
        try:
            # Fetch from chamber
            response = requests.get(f"{self.chamber_url}/spells")
            response.raise_for_status()
            remote_spells = response.json()
            spell_manifest = {spell['name']: spell for spell in remote_spells.get("spells", [])}

            click.echo("\n=== Spells Known to the Chamber ===")
            for spell in spell_manifest.values():
                formatted_desc = spell.get('formatted_description', f"{spell['name']} - {spell.get('description', 'No description')}")
                click.echo(formatted_desc)

            # List local spells
            click.echo("\n=== Spells Within Your Orb ===")
            spell_files = glob.glob(os.path.join(self.orb_dir, "*.spell"))
            if spell_files:
                for spell_path in spell_files:
                    spell_name = os.path.splitext(os.path.basename(spell_path))[0]
                    with open(spell_path, 'r') as f:
                        first_line = f.readline().strip()
                        if first_line.startswith('#'):
                            desc = first_line[1:].strip()
                        elif spell_name in spell_manifest:
                            desc = spell_manifest[spell_name].get('description', 'No description')
                        else:
                            desc = "No description"
                    click.echo(f"{spell_name}: {desc}")
            else:
                click.echo("Your orb lies dormant, waiting to capture mystical knowledge...")

        except requests.RequestException as e:
            click.echo(f"\nThe chamber is shrouded in mist... ({e})")
            # Still show local spells if remote fails
            spell_files = glob.glob(os.path.join(self.orb_dir, "*.spell"))
            if spell_files:
                for spell_path in spell_files:
                    spell_name = os.path.splitext(os.path.basename(spell_path))[0]
                    click.echo(spell_name)
            else:
                click.echo("Your orb lies dormant, waiting to capture mystical knowledge...")

    def _calculate_hash(self, content: str) -> str:
        """Calculate hash of spell content for comparison."""
        return hashlib.sha256(content.encode()).hexdigest()

@click.command()
@click.argument('args', nargs=-1)
@click.option('--archive', is_flag=True, help='Include archived spells in search')
def ponder(args, archive):
    """Explore available spells in your grimoire and the astral chamber.
    
    Ponder allows you to:
    \b
    - View all available spells locally and in the chamber
    - Search for specific spells by name
    - Examine spell details and requirements
    - Synchronize with the chamber to discover new spells
    """
    registry = SpellRegistry()
    
    if not args:
        click.echo(click.style("\nYou ponder the orb and gaze into the distant chamber...", fg="bright_magenta", bold=True))

        # Display chamber spells first
        manifest = registry.fetch_spell_manifest()
        if manifest and "spells" in manifest:
            click.echo(click.style("\n=== Spells Known to the Chamber ===", fg="bright_blue", bold=True))
            for spell_name, spell_info in manifest["spells"].items():
                alias = spell_info.get("alias", "")
                if alias == spell_name:  # Skip alias if it's the same as the name
                    alias = ""
                description = spell_info.get("description", "No description")
                
                # Format the output based on whether there's an alias
                if alias:
                    click.echo(click.style(f"{spell_name}", fg="magenta") + 
                             click.style(f" '{alias}' - ", fg="cyan") + 
                             click.style(description, fg="bright_white"))
                else:
                    click.echo(click.style(f"{spell_name} - ", fg="magenta") + 
                             click.style(description, fg="bright_white"))

        # Display orb spells (just names)
        orb_spells = glob.glob(os.path.join(registry.orb_dir, "*.spell"))
        if orb_spells:
            click.echo(click.style("\n=== Spells Within Your Orb ===", fg="bright_blue", bold=True))
            for orb_spell_path in orb_spells:
                spell_name = os.path.splitext(os.path.basename(orb_spell_path))[0]
                click.echo(click.style(f"{spell_name}", fg="magenta"))

        # Check for spells in orb that are not installed
        missing_spells = []
        for orb_spell_path in orb_spells:
            spell_name = os.path.splitext(os.path.basename(orb_spell_path))[0]
            spell_path = os.path.join(registry.spells_dir, f"{spell_name}.py")
            if not os.path.exists(spell_path):
                missing_spells.append(spell_name)

        if missing_spells:
            click.echo(click.style("\nYour orb holds spells that you have not yet mastered:", fg="bright_yellow", bold=True))
            for spell_name in missing_spells:
                click.echo(click.style(f"- {spell_name}", fg="yellow"))
            if click.confirm(click.style("Would you like to relearn them from the chamber?", fg="bright_yellow")):
                for spell_name in missing_spells:
                    result = registry.fetch_spell(spell_name)
                    if result:
                        content, _, requirements = result
                        registry.install_spell(spell_name, content, requirements)
                    else:
                        click.echo(click.style("Failed to relearn ", fg="red") + 
                                 click.style(f"'{spell_name}'", fg="bright_red"))
            else:
                click.echo(click.style("You decide to keep the knowledge latent within your orb.", fg="bright_magenta"))
        
        spell_name = click.prompt(
            click.style("\nWhich spell would you like to ponder?", fg="bright_yellow") + 
            click.style(" (or 'sync' to synchronize with chamber)", fg="yellow"), 
            type=str
        )

        if spell_name.lower() == 'sync':
            click.echo("Initiating mystical synchronization...")
            registry.sync_spells()
            return

        # Check if spell is installed
        installed_spell_path = os.path.join(registry.spells_dir, f"{spell_name}.py")
        if os.path.exists(installed_spell_path):
            click.echo(f"\nYou have already mastered the '{spell_name}' spell.")
            if click.confirm("Would you like to unlearn it?"):
                registry.uninstall_spell(spell_name)
            else:
                click.echo(f"You continue to wield the power of '{spell_name}'.")
            return

        # Try local first
        local_path = os.path.join(registry.orb_dir, f"{spell_name}.spell")
        if os.path.exists(local_path):
            with open(local_path, 'r') as f:
                content = f.read()
            # Extract requirements from the local content
            requirements = registry.extract_requirements(content)
            if not archive and click.confirm("\nYour orb resonates with this knowledge. Would you like to master this spell?"):
                registry.install_spell(spell_name, content, requirements)
        else:
            # Try remote
            result = registry.fetch_spell(spell_name)
            if result:
                content, spell_hash, requirements = result
                # Fetch description from manifest
                manifest = registry.fetch_spell_manifest()
                description = manifest.get("spells", {}).get(spell_name, {}).get("description", "")
                if archive:
                    if click.confirm("\nWould you like to preserve this knowledge in your orb?"):
                        registry.save_to_orb(spell_name, content, description)
                else:
                    click.echo("\nYou begin to meditate on the ancient knowledge...")
                    if registry.install_spell(spell_name, content, requirements):
                        # Also save to orb for reference
                        registry.save_to_orb(spell_name, content, description)
            else:
                click.echo(f"\nThe mysteries of '{spell_name}' remain hidden from both your orb and the distant chamber.")

    else:
        # Direct spell lookup/install mode
        spell_name = args[0]
        installed_spell_path = os.path.join(registry.spells_dir, f"{spell_name}.py")
        if os.path.exists(installed_spell_path):
            click.echo(f"\nYou have already mastered the '{spell_name}' spell.")
            if click.confirm("Would you like to unlearn it?"):
                registry.uninstall_spell(spell_name)
            else:
                click.echo(f"You continue to wield the power of '{spell_name}'.")
            return

        result = registry.fetch_spell(spell_name)

        if result:
            content, spell_hash, requirements = result
            # Fetch description from manifest
            manifest = registry.fetch_spell_manifest()
            description = manifest.get("spells", {}).get(spell_name, {}).get("description", "")
            if archive:
                registry.save_to_orb(spell_name, content, description)
            else:
                click.echo("\nYou begin to meditate on the ancient knowledge...")
                if registry.install_spell(spell_name, content, requirements):
                    # Also save to orb for reference
                    registry.save_to_orb(spell_name, content, description)
        else:
            click.echo(f"\nThe mysteries of '{spell_name}' remain hidden.")

alias = "pd"

def main():
    ponder()

if __name__ == '__main__':
    main()
