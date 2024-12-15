#!/usr/bin/env python3

import click
import sys
import yaml
import hashlib
import shutil
import tempfile
import subprocess
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from magi_cli.loci.spellcraft.spell_bundle import SpellBundle
from magi_cli.loci.spellcraft.spell_builder import SpellBuilder
from magi_cli.spells import SANCTUM_PATH

class SpellRecipe:
    """Handles the creation and bundling of different spell types."""
    
    def __init__(self, spell_name: str, spell_type: str):
        """
        Initialize a spell recipe.
        
        Args:
            spell_name (str): Name of the spell
            spell_type (str): Type of the spell (e.g., 'macro', 'script', 'bundled')
        """
        self.spell_name = spell_name
        self.spell_type = spell_type
        self.temp_dir = Path(tempfile.mkdtemp(prefix='spell_recipe_'))
        self.spell_dir = self.temp_dir / spell_name
        
        # Clean up any existing directories
        if self.spell_dir.exists():
            shutil.rmtree(self.spell_dir)
            
        # Create fresh directories with proper permissions
        self.spell_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir = self.spell_dir / 'artifacts'
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.spell_subdir = self.spell_dir / 'spell'
        self.spell_subdir.mkdir(parents=True, exist_ok=True)
        
        # Add tome_dir attribute
        self.tome_dir = Path(SANCTUM_PATH) / '.tome'
        self.tome_dir.mkdir(parents=True, exist_ok=True)

    def _generate_metadata(self, description: str, entry_point: str, shell_type: str = "python") -> dict:
        """Generate standard metadata for the spell."""
        metadata = {
            "name": self.spell_name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "type": self.spell_type,
            "shell_type": shell_type,
            "entry_point": entry_point,
            "version": "1.0.0"
        }
        return metadata

    def _create_yaml_config(self, metadata: dict, additional_config: Optional[Dict] = None) -> None:
        """Create the spell.yaml configuration file."""
        config = {
            'name': metadata['name'],
            'version': metadata['version'],
            'description': metadata['description'],
            'type': metadata['type'],
            'shell_type': metadata['shell_type'],
            'entry_point': metadata['entry_point']
        }
        if additional_config:
            config.update(additional_config)
            
        yaml_path = self.spell_subdir / 'spell.yaml'
        with open(yaml_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

    def _fetch_artifact(self, artifact_config: Dict[str, Any], base_path: Path) -> None:
        """Fetch an artifact from various sources."""
        path = base_path / artifact_config['path']
        path.parent.mkdir(parents=True, exist_ok=True)

        if 'content' in artifact_config:
            # Direct content specification
            path.write_text(artifact_config['content'])
            return

        if 'source' not in artifact_config:
            raise ValueError(f"Artifact {path} must have either 'content' or 'source' specified")

        source = artifact_config['source']
        source_type = source['type']
        location = source['location']

        if source_type == 'url':
            # Download from URL
            response = requests.get(location)
            response.raise_for_status()
            path.write_bytes(response.content)

        # TODO: Investigate and test 
        elif source_type == 'git':
            # Clone from git repository
            import git
            temp_dir = Path(tempfile.mkdtemp())
            repo = git.Repo.clone_from(location, temp_dir)
            if 'ref' in source:
                repo.git.checkout(source['ref'])
            
            # Copy specific file or entire directory
            source_path = temp_dir
            if 'file' in source:
                source_path = source_path / source['file']
                shutil.copy2(source_path, path)
            else:
                if path.exists():
                    shutil.rmtree(path)
                shutil.copytree(source_path, path)
            shutil.rmtree(temp_dir)

        elif source_type == 'file':
            # Copy from local file
            source_path = Path(location).expanduser().resolve()
            if not source_path.exists():
                raise FileNotFoundError(f"Local file not found: {source_path}")
            shutil.copy2(source_path, path)

        elif source_type == 'curl':
            # Use curl with custom headers
            import subprocess
            headers = source.get('headers', {})
            cmd = ['curl', '-L', '-o', str(path)]
            for key, value in headers.items():
                cmd.extend(['-H', f'{key}: {value}'])
            cmd.append(location)
            subprocess.run(cmd, check=True)

        else:
            raise ValueError(f"Unknown source type: {source_type}")


    # TODO: Is this a duplicate of _fetch_artifact?
    def _fetch_remote_artifact(self, url: str, filename: str) -> Path:
        """Fetch a remote artifact and save it to the artifacts directory."""
        response = requests.get(url)
        response.raise_for_status()
        artifact_path = self.artifacts_dir / filename
        with open(artifact_path, 'wb') as f:
            f.write(response.content)
        return artifact_path

    def create_bundled_spell(self, source_dir: Path, description: str = None) -> Path:
        """Create a bundled spell from an existing directory that ends in '.spell/'."""
        # Check for existing spell.yaml and use its config if available
        yaml_path = source_dir / 'spell' / 'spell.yaml'
        if yaml_path.exists():
            with open(yaml_path) as f:
                config = yaml.safe_load(f)
                
            # Clear any existing content in spell directory
            if self.spell_dir.exists():
                shutil.rmtree(self.spell_dir)
            self.spell_dir.mkdir(parents=True)
                
            # Copy contents preserving the correct structure
            for item in source_dir.iterdir():
                if item.is_file():
                    shutil.copy2(item, self.spell_dir / item.name)
                elif item.is_dir():
                    # Special handling for spell and artifacts directories
                    if item.name in ['spell', 'artifacts']:
                        dest_dir = self.spell_dir / item.name
                        shutil.copytree(item, dest_dir, dirs_exist_ok=True)
                    else:
                        # Other directories go under spell directory
                        dest_dir = self.spell_dir / 'spell' / item.name
                        shutil.copytree(item, dest_dir, dirs_exist_ok=True)
                    
            # Convert dependencies to requires list
            requires = []
            if 'requires' in config:
                requires = config['requires'] if isinstance(config['requires'], list) else [config['requires']]
            elif 'dependencies' in config and 'python' in config['dependencies']:
                requires = config['dependencies']['python']
            
            # Create yaml config with requires
            yaml_config = {
                'name': config['name'],
                'type': config['type'],
                'shell_type': config.get('shell_type', 'python'),
                'entry_point': config['entry_point'].replace('spell/', ''),  # Remove spell/ prefix
                'description': config['description'],
                'requires': requires,
                'version': config.get('version', '1.0.0')
            }
            
            # Check for missing dependencies
            if requires:
                try:
                    import importlib.util
                    missing_deps = []
                    
                    for dep in requires:
                        pkg_name = dep.split('>=')[0].split('~=')[0].split('==')[0].strip()
                        try:
                            spec = importlib.util.find_spec(pkg_name)
                            if spec is None:
                                missing_deps.append(dep)
                        except ImportError:
                            missing_deps.append(dep)
                            
                    if missing_deps:
                        if click.get_current_context().params.get('verbose', False):
                            click.echo("\nMissing required packages:")
                            for dep in missing_deps:
                                click.echo(f"  - {dep}")
                        
                        if click.confirm("\nWould you like to install these dependencies now?", default=True):
                            try:
                                subprocess.run([sys.executable, '-m', 'pip', 'install', *missing_deps], check=True)
                                if click.get_current_context().params.get('verbose', False):
                                    click.echo("Dependencies installed successfully.")
                            except subprocess.CalledProcessError as e:
                                click.echo(f"Warning: Failed to install dependencies: {e}")
                                if not click.confirm("\nWould you like to continue without installing dependencies?", default=False):
                                    raise ValueError("Cannot proceed: missing required dependencies")
                        elif not click.confirm("\nWould you like to continue without installing dependencies?", default=False):
                            raise ValueError("Cannot proceed: missing required dependencies")
                            
                except Exception as e:
                    click.echo(f"Warning: Could not check dependencies: {e}")
                    if not click.confirm("\nWould you like to continue without checking dependencies?", default=False):
                        raise ValueError("Cannot proceed: unable to check dependencies")
            
            # Write yaml config
            yaml_path = self.spell_dir / 'spell' / 'spell.yaml'
            yaml_path.parent.mkdir(parents=True, exist_ok=True)
            with open(yaml_path, 'w') as f:
                yaml.dump(yaml_config, f, default_flow_style=False)
            
            # Copy entry point script from the correct location
            source_script = source_dir / 'spell' / yaml_config['entry_point']
            target_script = self.spell_dir / 'spell' / yaml_config['entry_point']
            if source_script.exists():
                target_script.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_script, target_script)
            else:
                raise ValueError(f"Entry point script not found: {source_script}")
            
            # Use SpellBundle.create_spell_bundle for proper bundling
            bundle = SpellBundle(self.spell_dir)
            return bundle.create_spell_bundle(
                spell_name=config['name'],
                spell_type=config['type'],
                shell_type=config.get('shell_type', 'python'),
                entry_point=yaml_config['entry_point'],  # Use the updated entry point
                description=config['description'],
                spell_dir=self.spell_dir,
                verify_structure=False  # Skip structure verification since we copied exactly
            )
        
        # If no spell.yaml exists, fallback to manual bundling
        if not description:
            description = click.prompt("Enter spell description")

        # Copy all contents to spell directory
        for item in source_dir.glob('*'):
            if item.is_file():
                shutil.copy2(item, self.spell_subdir)
            elif item.is_dir():
                shutil.copytree(item, self.spell_subdir / item.name)

        # Create metadata and config
        metadata = self._generate_metadata(description, "spell/main.py")
        additional_config = {
            'requires': [],  # Add empty requires list for new spells
            'version': '1.0.0'
        }
        self._create_yaml_config(metadata, additional_config)
        
        return self._bundle_spell(metadata)

    def create_macro_spell(self, commands: List[str], description: str) -> Path:
        """
        Create a macro spell with a list of commands.
        
        Args:
            commands (List[str]): List of commands to execute
            description (str): Description of the macro spell
        
        Returns:
            Path: Path to the created spell bundle
        """

        #TODO: We need to generate metadata for macro spells better
        # Prepare metadata
        metadata = {
            'name': self.spell_name,
            'description': description,
            'type': 'macro',
            'shell_type': 'bash',
            'version': '1.0.0',
            'commands': commands,  # Store commands in metadata
            'entry_point': f'spell/{self.spell_name}.sh'
        }


        # TODO: We need to generalize this structure and make it more dynamic across all spell types
        # Create spell directory structure
        spell_dir = self.temp_dir / self.spell_name
        spell_dir.mkdir(parents=True, exist_ok=True)
        spell_subdir = spell_dir / 'spell'
        spell_subdir.mkdir(parents=True, exist_ok=True)
        artifacts_dir = spell_dir / 'artifacts'
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Create macro script
        macro_script_path = spell_subdir / f'{self.spell_name}.sh'
        with open(macro_script_path, 'w') as f:
            f.write('#!/bin/bash\n')
            for cmd in commands:
                f.write(f"{cmd}\n")
        
        # Make script executable
        macro_script_path.chmod(0o755)
        
        # Write spell.yaml
        yaml_path = spell_subdir / 'spell.yaml'
        with open(yaml_path, 'w') as f:
            yaml.safe_dump(metadata, f, default_flow_style=False)
        
        # Create spell bundle
        spell_bundle = SpellBundle(spell_dir)
        bundle_path = spell_bundle.create_bundle(self.tome_dir)
        
        return bundle_path

    def create_script_spell(self, script_path: Path, description: str) -> Path:
        """Create a spell from a Python or Shell script."""
        # Determine shell type
        shell_type = "python" if script_path.suffix == '.py' else "bash"
        
        # Copy script to spell directory
        spell_script_path = self.spell_subdir / script_path.name
        shutil.copy2(script_path, spell_script_path)
        if shell_type == "bash":
            spell_script_path.chmod(0o755)

        # TODO: This looks like a better method of creating metadata
        # Create metadata and config
        metadata = self._generate_metadata(description, f"spell/{script_path.name}", shell_type)
        self._create_yaml_config(metadata)
        
        return self._bundle_spell(metadata)

    def _bundle_spell(self, metadata: dict) -> Path:
        """Bundle the spell directory into a .spell file."""
        bundle = SpellBundle(self.spell_dir)
        try:
            return bundle.create_bundle(self.tome_dir)
        finally:
            shutil.rmtree(self.temp_dir)

def get_success_message(message: str) -> str:
    """Get a success message with appropriate emoji and color."""
    return click.style(f"✨ {message}", fg="bright_green", bold=True)

def get_mystical_prompt(message: str, prompt_type: str = "input") -> str:
    """Get a mystically styled prompt message."""
    symbols = {
        "description": "»",
        "command": "»",
        "info": "»",
        "warning": "!",
        "success": "✨"
    }
    symbol = symbols.get(prompt_type, "»")
    return click.style(f"{symbol} {message}", fg="bright_magenta", bold=True)

@click.command()
@click.argument('args', nargs=-1)
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose output')
def spellcraft(args, verbose):
    """Craft different types of spells based on input.
    
    Create spells from commands, scripts, or configuration files:
    
    \b
    Macro Spells:   Combine multiple shell commands into a single spell
    Script Spells:  Convert Python or Bash scripts into spells
    Config Spells:  Create spells from YAML configuration files
    """
    try:
        if not args:
            click.echo(click.style("Available Spell Types:", fg="bright_blue", bold=True))
            click.echo(click.style("  Macro Spell:", fg="cyan") + " cast sc <number_of_commands> <spell_name>")
            click.echo(click.style("  Script Spell:", fg="cyan") + " cast sc <path> [spell_name]")
            click.echo(click.style("  Config Spell:", fg="cyan") + " cast sc <config.yaml>")
            return

        try:
            num_commands = int(args[0])
            if len(args) < 2:
                raise click.UsageError("Spell name required for macro spells")
            spell_name = args[1]

            click.echo(click.style("\nBeginning spellcraft...", fg="bright_magenta", bold=True))
            description = click.prompt(get_mystical_prompt("Enter spell description", "description"))
            
            click.echo(click.style("\nGathering commands...", fg="bright_blue", bold=True))
            commands = []
            for i in range(num_commands):
                cmd = click.prompt(get_mystical_prompt(f"Command {i + 1}", "command"))
                commands.append(cmd)
                click.echo(click.style("Command recorded", fg="bright_green"))

            click.echo(click.style("\nGenerating spell...", fg="bright_yellow", bold=True))
            recipe = SpellRecipe(spell_name, "macro")
            bundle_path = recipe.create_macro_spell(commands, description)
            
            # Simplified sigil message
            sigil_path = f"{recipe.temp_dir}/{spell_name}/{spell_name}_sigil.svg"
            click.echo(click.style("Generating sigil at:", fg="bright_blue", bold=True) + 
                      click.style(f" {sigil_path}", fg="cyan"))
            
            click.echo(get_success_message(f"Spell crafted successfully: {bundle_path}"))
            return
        except ValueError:
            pass  # Not a number, try other spell types

        # Handle other spell types
        input_path = Path(args[0])
        spell_name = args[1] if len(args) > 1 else None

        if input_path.suffix == '.yaml':
            try:
                # Load the YAML config
                with open(input_path) as f:
                    yaml_config = yaml.safe_load(f)
                
                # Use the name from YAML or fallback to filename
                spell_name = spell_name or yaml_config.get('name') or input_path.stem
                description = yaml_config.get('description')
                
                if not description:
                    description = click.prompt("Enter spell description")

                # Create as bundled spell
                recipe = SpellRecipe(spell_name, "bundled")
                
                # Create temporary spell directory structure
                temp_spell_dir = Path(tempfile.mkdtemp()) / f"{spell_name}.spell"
                temp_spell_dir.mkdir(parents=True)
                
                # Let SpellBuilder handle the content creation
                builder = SpellBuilder(input_path)
                builder.create_spell_structure(temp_spell_dir)
                
                # Use same bundling process as other spell types
                bundle_path = recipe.create_bundled_spell(temp_spell_dir, description)
                
                # Clean up temp directory
                shutil.rmtree(temp_spell_dir.parent)
                
                click.echo(get_success_message(f"Spell crafted successfully: {bundle_path}"))
                return
            except Exception as e:
                raise click.UsageError(f"Failed to build spell from YAML: {str(e)}")

        elif input_path.suffix in ['.py', '.sh']:
            spell_name = spell_name or input_path.stem
            description = click.prompt("Enter spell description")

            recipe = SpellRecipe(spell_name, "script")
            bundle_path = recipe.create_script_spell(input_path, description)

        elif input_path.is_dir() and input_path.name.endswith('.spell'):
            spell_name = spell_name or input_path.stem
            # For bundled spells, try to get description from spell.yaml first
            yaml_path = input_path / 'spell' / 'spell.yaml'
            if yaml_path.exists():
                try:
                    with open(yaml_path) as f:
                        spell_yaml = yaml.safe_load(f)
                        description = spell_yaml.get('description', '')
                except Exception:
                    description = None
            
            if not description:
                description = click.prompt("Enter spell description")

            recipe = SpellRecipe(spell_name, "bundled")
            bundle_path = recipe.create_bundled_spell(input_path, description)
        else:
            raise click.UsageError(
                "Invalid input. Must be:\n"
                "- Use -n <number> for macro spells\n"
                "- A .yaml file for configured spells\n"
                "- A .py or .sh script file\n"
                "- A .spell directory for bundled spells"
            )

        click.echo(get_success_message(f"Spell crafted successfully: {bundle_path}"))

    except Exception as e:
        click.echo(f"Error crafting spell: {str(e)}", err=True)
        sys.exit(1)

alias = "sc"

if __name__ == '__main__':
    spellcraft()