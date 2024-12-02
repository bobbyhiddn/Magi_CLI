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
        # Load and validate YAML
        with open(self.yaml_path) as f:
            config = yaml.safe_load(f)

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

        # Create the main script
        if 'code' in config:
            # Determine file extension based on shell_type
            ext = '.py' if config['shell_type'] == 'python' else '.sh'
            main_script = f"main{ext}"
            script_path = spell_subdir / main_script
            script_path.write_text(config['code'])
            if config['shell_type'] != 'python':
                script_path.chmod(0o755)
        else:
            raise ValueError("No code specified in YAML")

        # Handle dependencies if specified
        if 'requires' in config:
            requirements_path = spell_dir / 'requirements.txt'
            requirements_path.write_text('\n'.join(config['requires']))
            
            # Install dependencies into the system Python
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(requirements_path)], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Warning: Failed to install dependencies: {e}")

        # Handle artifacts
        if 'artifacts' in config:
            for artifact in config['artifacts']:
                self._fetch_artifact(artifact, spell_dir)

        # Create spell.yaml
        spell_yaml = {
            'name': config['name'],
            'version': config.get('version', '1.0.0'),
            'description': config['description'],
            'type': config['type'],
            'shell_type': config['shell_type'],
            'entry_point': f"spell/{main_script}"
        }
        
        # Add any additional configuration
        for key, value in config.items():
            if key not in ['code', 'artifacts', 'requires']:
                spell_yaml[key] = value
                
        yaml_path = spell_subdir / 'spell.yaml'
        with open(yaml_path, 'w') as f:
            yaml.dump(spell_yaml, f, default_flow_style=False)

        # Create the bundle
        bundle = SpellBundle(spell_dir)
        tome_dir = Path(SANCTUM_PATH) / '.tome'
        tome_dir.mkdir(parents=True, exist_ok=True)
        return bundle.create_bundle(tome_dir)

    def __del__(self):
        """Clean up temporary directory."""
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
