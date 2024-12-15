#!/usr/bin/env python3

import yaml
import shutil
import tempfile
import requests
import subprocess
import click
from pathlib import Path
from typing import Dict, Any, Optional
from magi_cli.loci.spellcraft.spell_bundle import SpellBundle
from magi_cli.spells import SANCTUM_PATH

class SpellBuilder:
   def __init__(self, yaml_path: Path):
       self.yaml_path = yaml_path
       self.temp_dir = Path(tempfile.mkdtemp(prefix='spell_builder_'))
       self.tome_dir = Path(SANCTUM_PATH) / '.tome'
       self.tome_dir.mkdir(parents=True, exist_ok=True)

   def create_spell_structure(self, spell_dir: Path) -> None:
       with open(self.yaml_path) as f:
           config = yaml.safe_load(f)

       spell_subdir = spell_dir / 'spell'
       artifacts_dir = spell_dir / 'artifacts'
       spell_subdir.mkdir(parents=True)
       artifacts_dir.mkdir(parents=True)

       if 'code' in config:
           entry_point = config.get('entry_point', 'main.py')
           script_path = spell_subdir / entry_point
           click.echo(click.style("  » Adding:", fg="bright_blue") + 
                     click.style(f" spell\\{entry_point}", fg="cyan"))
           script_path.write_text(config['code'])
           if config.get('shell_type') != 'python':
               script_path.chmod(0o755)

       # Handle dependencies consistently
       dependencies = {}
       if 'requires' in config:
           dependencies['python'] = config['requires'] if isinstance(config['requires'], list) else [config['requires']]
       elif 'dependencies' in config:
           dependencies = config['dependencies']

       spell_yaml = {
           'name': config['name'],
           'description': config['description'],
           'type': 'bundled',
           'shell_type': config.get('shell_type', 'python'), 
           'version': config.get('version', '1.0.0'),
           'entry_point': config.get('entry_point', 'main.py'),
           'dependencies': dependencies
       }

       yaml_path = spell_subdir / 'spell.yaml'
       click.echo(click.style("  » Adding:", fg="bright_blue") + 
                 click.style(" spell\\spell.yaml", fg="cyan"))
       with open(yaml_path, 'w') as f:
           yaml.safe_dump(spell_yaml, f, default_flow_style=False)

       if 'artifacts' in config:
           for artifact in config['artifacts']:
               self._fetch_artifact(artifact, spell_dir)
               click.echo(click.style("  » Adding:", fg="bright_blue") + 
                         click.style(f" artifacts\\{artifact['path']}", fg="cyan"))

   def _fetch_artifact(self, artifact_config: Dict[str, Any], base_path: Path) -> None:
       path = base_path / 'artifacts' / artifact_config['path']
       path.parent.mkdir(parents=True, exist_ok=True)

       if 'content' in artifact_config:
           path.write_text(artifact_config['content'])
           if path.parts[-2] == 'templates' and path.suffix == '.html':
               template_dir = base_path / 'spell' / 'templates'
               template_dir.mkdir(parents=True, exist_ok=True)
               shutil.copy2(path, template_dir / path.name)
           return

       if 'source' not in artifact_config:
           raise ValueError(f"Artifact {path} must have either 'content' or 'source'")

       source = artifact_config['source']
       source_type = source['type']
       location = source['location']

       if source_type == 'url':
           response = requests.get(location)
           response.raise_for_status()
           path.write_bytes(response.content)
       elif source_type == 'file':
           source_path = Path(location).expanduser().resolve()
           if not source_path.exists():
               raise FileNotFoundError(f"Local file not found: {source_path}")
           shutil.copy2(source_path, path)
       elif source_type == 'curl':
           headers = source.get('headers', {})
           cmd = ['curl', '-L', '-o', str(path)] + sum([['-H', f'{k}: {v}'] for k, v in headers.items()], []) + [location]
           subprocess.run(cmd, check=True)
       else:
           raise ValueError(f"Unknown source type: {source_type}")

   def build(self) -> Path:
       yaml_path = self.yaml_path
       if yaml_path.is_dir():
           yaml_path = yaml_path / 'spell' / 'spell.yaml'
           if not yaml_path.exists():
               yaml_path = self.yaml_path / 'spell.yaml'

       with open(yaml_path) as f:
           config = yaml.safe_load(f)

       spell_dir = self.temp_dir / f"{config['name']}.spell"
       print("- Adding files to bundle:")
       self.create_spell_structure(spell_dir)

       bundle = SpellBundle(spell_dir)
       return bundle.create_bundle(self.tome_dir)

   def __del__(self):
       if self.temp_dir and self.temp_dir.exists():
           shutil.rmtree(self.temp_dir)