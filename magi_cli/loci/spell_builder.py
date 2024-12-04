#!/usr/bin/env python3

import yaml
import shutil
import tempfile
import requests
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from magi_cli.modules.spell_bundle import SpellBundle
from magi_cli.spells import SANCTUM_PATH
import click

class SpellBuilder:
    """Builds spells from YAML configurations with support for various artifact sources."""
    
    def __init__(self, yaml_path: Path):
        """Initialize builder with YAML configuration path."""
        self.yaml_path = yaml_path
        self.temp_dir = Path(tempfile.mkdtemp(prefix='spell_builder_'))
        
        # Add tome_dir for compatibility
        self.tome_dir = Path(SANCTUM_PATH) / '.tome'
        self.tome_dir.mkdir(parents=True, exist_ok=True)

    def _fetch_artifact(self, artifact_config: Dict[str, Any], base_path: Path) -> None:
        """Fetch an artifact from various sources."""
        # Ensure artifacts go into the artifacts directory
        path = base_path / 'artifacts' / artifact_config['path']
        path.parent.mkdir(parents=True, exist_ok=True)

        if 'content' in artifact_config:
            # Direct content specification
            path.write_text(artifact_config['content'])
            
            # For Flask templates, also copy to spell directory
            if path.parts[-2] == 'templates' and path.suffix == '.html':
                template_dir = base_path / 'spell' / 'templates'
                template_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, template_dir / path.name)
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
            headers = source.get('headers', {})
            cmd = ['curl', '-L', '-o', str(path)]
            for key, value in headers.items():
                cmd.extend(['-H', f'{key}: {value}'])
            cmd.append(location)
            subprocess.run(cmd, check=True)

        else:
            raise ValueError(f"Unknown source type: {source_type}")

    def build(self) -> Path:
        """Build a spell from the YAML configuration."""
        yaml_path = self.yaml_path
        if yaml_path.is_dir():
            yaml_path = yaml_path / 'spell' / 'spell.yaml'
            if not yaml_path.exists():
                yaml_path = self.yaml_path / 'spell.yaml'
            click.echo(f"\nCreating spell bundle:")
            
        # Load and validate YAML
        with open(yaml_path) as f:
            config = yaml.safe_load(f)
            
        click.echo(f"- Name: {config.get('name', 'Unnamed Spell')}")
        click.echo(f"- Type: {config.get('type', 'script')}")
        click.echo(f"- Entry point: {config.get('entry_point', 'None')}")

        # Set default values if not provided
        config.setdefault('name', yaml_path.stem)
        config.setdefault('description', 'No description provided')
        config.setdefault('type', 'script')
        config.setdefault('shell_type', 'python')
        config.setdefault('version', '1.0.0')

        # Create spell directory structure
        spell_dir = self.temp_dir / config['name']
        spell_dir.mkdir(parents=True, exist_ok=True)
        spell_subdir = spell_dir / 'spell'
        spell_subdir.mkdir(parents=True, exist_ok=True)
        artifacts_dir = spell_dir / 'artifacts'
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Handle inline code case
        if 'code' in config:
            # Determine file extension based on shell_type
            ext = '.py' if config.get('shell_type', 'python') == 'python' else '.sh'
            main_script = f"main{ext}"
            script_path = spell_subdir / main_script
            script_path.write_text(config['code'])
            
            # Make script executable for non-python scripts
            if config.get('shell_type', 'python') != 'python':
                script_path.chmod(0o755)
            
            # Update entry point
            config['entry_point'] = main_script

        # Ensure entry point exists
        if not config.get('entry_point'):
            raise ValueError("No entry point specified or generated")

        # Write spell.yaml to the spell subdirectory
        spell_yaml_path = spell_subdir / 'spell.yaml'
        with open(spell_yaml_path, 'w') as f:
            yaml.safe_dump(config, f, default_flow_style=False)

        # Create spell bundle using unified method
        bundle = SpellBundle(spell_dir)  
        bundle_path = bundle.create_spell_bundle(
            spell_name=config['name'],
            spell_type=config['type'],
            shell_type=config.get('shell_type', 'python'),
            entry_point=config['entry_point'],
            description=config['description'],
            spell_dir=spell_subdir,  
            verify_structure=False  
        )
        return bundle_path

    def __del__(self):
        """Clean up temporary directory."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
