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
            click.echo(f"\nCreating spell bundle:")
            
        # Load and validate YAML
        with open(yaml_path) as f:
            config = yaml.safe_load(f)
            
        click.echo(f"- Name: {config.get('name')}")
        click.echo(f"- Type: {config.get('type')}")
        click.echo(f"- Entry point: {config.get('entry_point')}")

        required_fields = ['name', 'description', 'type', 'shell_type']
        missing = [field for field in required_fields if field not in config]
        if missing:
            raise ValueError(f"Missing required fields in YAML: {', '.join(missing)}")

        # Create spell directory structure
        spell_dir = self.temp_dir / config['name']
        spell_dir.mkdir(parents=True)
        spell_subdir = spell_dir / 'spell'
        spell_subdir.mkdir()
        artifacts_dir = spell_dir / 'artifacts'
        artifacts_dir.mkdir()

        # Handle dependencies if specified
        requires = config.get('requires', [])
        if not isinstance(requires, list):
            click.echo(f"Warning: requires field is not a list: {requires}")
            if isinstance(requires, str):
                requires = [requires]
            else:
                requires = []
            
        if requires:
            # Create requirements.txt in the spell directory
            requirements_path = spell_dir / 'requirements.txt'
            requirements_path.write_text('\n'.join(requires))
            
            # Convert to standardized metadata format and update config
            config['dependencies'] = {'python': requires}
            
            # Check for missing dependencies
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
                    click.echo("\nMissing required packages:")
                    for dep in missing_deps:
                        click.echo(f"  - {dep}")
                        
                    if click.confirm("\nWould you like to install these dependencies now?", default=True):
                        try:
                            click.echo("\nInstalling dependencies...")
                            subprocess.run([sys.executable, '-m', 'pip', 'install', *missing_deps], check=True)
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

        # Handle source files for directory-based spells
        if self.yaml_path.is_dir():
            click.echo(f"- Base dir: {spell_dir}")
            click.echo(f"- Created nested dir: {spell_subdir}")
            
            # Copy entry point script, handling spell/ prefix
            entry_point = config.get('entry_point', 'analyzer.py')
            entry_point = entry_point.replace('spell/', '')  # Remove spell/ prefix if present
            
            # Try both with and without spell/ directory
            source_script = self.yaml_path / 'spell' / entry_point
            if not source_script.exists():
                source_script = self.yaml_path / entry_point
                if not source_script.exists():
                    raise ValueError(f"Entry point script not found at {source_script} or {self.yaml_path / 'spell' / entry_point}")
                    
            target_script = spell_subdir / entry_point.split('/')[-1]
            
            click.echo(f"- Moving from: {source_script}")
            click.echo(f"- Moving to: {target_script}")
            shutil.copy2(source_script, target_script)
            
            # Copy spell.yaml
            click.echo("- Writing spell.yaml")
            yaml_path = self.yaml_path / 'spell' / 'spell.yaml'
            if not yaml_path.exists():
                yaml_path = self.yaml_path / 'spell.yaml'
                if not yaml_path.exists():
                    raise ValueError(f"spell.yaml not found at {yaml_path} or {self.yaml_path / 'spell' / 'spell.yaml'}")
            shutil.copy2(yaml_path, spell_subdir / 'spell.yaml')
            
            # Copy artifacts if they exist
            source_artifacts = self.yaml_path / 'artifacts'
            if source_artifacts.exists():
                shutil.copytree(source_artifacts, artifacts_dir, dirs_exist_ok=True)
        else:
            # Handle inline code case
            if 'code' not in config:
                raise ValueError("No code specified in YAML")
                
            # Determine file extension based on shell_type
            ext = '.py' if config['shell_type'] == 'python' else '.sh'
            main_script = f"main{ext}"
            script_path = spell_subdir / main_script
            script_path.write_text(config['code'])
            if config['shell_type'] != 'python':
                script_path.chmod(0o755)

            # Handle artifacts if specified in YAML
            if 'artifacts' in config:
                for artifact in config['artifacts']:
                    self._fetch_artifact(artifact, spell_dir)

        # Create bundle
        bundle = SpellBundle(spell_dir)
        tome_dir = Path(SANCTUM_PATH) / '.tome'
        tome_dir.mkdir(parents=True, exist_ok=True)
        return bundle.create_bundle(tome_dir)

    def __del__(self):
        """Clean up temporary directory."""
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
