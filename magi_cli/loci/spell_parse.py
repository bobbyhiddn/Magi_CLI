# magi_cli/modules/spell_parse.py
import os
import json
import zipfile
import tempfile
import hashlib
import subprocess
import sys
import click  # Ensure click is imported
import shutil
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from magi_cli.spells import SANCTUM_PATH

class SpellParser:
    """Parser for spell bundles with enhanced validation."""
    
    # Required metadata fields
    REQUIRED_FIELDS = ['name', 'version', 'description', 'type', 'entry_point']
    ALLOWED_TYPES = ['bundled', 'macro', 'script']  # Updated to include 'script'
    ALLOWED_SHELLS = ['python', 'bash', 'shell']
    ALLOWED_EXTENSIONS = ['.py', '.sh', '.spell', '.fiat']  # Added extensions list
    
    @staticmethod
    def parse_bundle(spell_path: Path) -> Tuple[Path, Dict[str, Any]]:
        """Parse and validate a spell bundle, returning extracted path and metadata."""
        if not spell_path.exists():
            raise ValueError(f"Spell file not found: {spell_path}")
            
        temp_dir = Path(tempfile.mkdtemp(prefix='magi_spell_'))
        try:
            with zipfile.ZipFile(spell_path, 'r') as zf:
                zf.extractall(temp_dir)
                
                # Check metadata in spell.json first
                metadata_path = temp_dir / 'spell.json'
                if (metadata_path.exists()):
                    metadata = json.loads(metadata_path.read_text())
                    SpellParser._validate_metadata(metadata)
                    return temp_dir, metadata
                    
                # Try legacy spell.yaml format
                yaml_path = temp_dir / 'spell' / 'spell.yaml'
                if yaml_path.exists():
                    import yaml
                    with open(yaml_path) as f:
                        config = yaml.safe_load(f)
                    metadata = SpellParser._convert_yaml_to_metadata(config)
                    SpellParser._validate_metadata(metadata)
                    return temp_dir, metadata
                    
                raise ValueError("No valid metadata found in spell bundle")
                
        except zipfile.BadZipFile:
            # Handle macro spells (simple command files)
            if spell_path.exists():
                content = spell_path.read_text()
                first_line = content.splitlines()[0] if content else ''
                description = first_line[1:].strip() if first_line.startswith('#') else ''
                
                metadata = {
                    "name": spell_path.stem,
                    "type": "macro",
                    "shell_type": "shell",
                    "description": description,
                    "version": "1.0.0",
                    "entry_point": spell_path.name,
                    "sigil_hash": SpellParser.calculate_sigil_hash(spell_path)
                }
                SpellParser._validate_metadata(metadata)
                return temp_dir, metadata
                    
            raise ValueError("Invalid spell format")
            
    @staticmethod
    def _validate_metadata(metadata: Dict[str, Any]) -> None:
        """Validate spell metadata contains required fields and valid values."""
        # Allow either entry_point or main_script
        if 'main_script' in metadata and 'entry_point' not in metadata:
            metadata['entry_point'] = metadata['main_script']
        
        # Check required fields
        missing = [field for field in SpellParser.REQUIRED_FIELDS if field not in metadata]
        if missing:
            raise ValueError(f"Missing required metadata fields: {', '.join(missing)}")
            
        # Add type validation that supports all spell types    
        if metadata.get('type') not in SpellParser.ALLOWED_TYPES:
            raise ValueError(f"Invalid spell type: {metadata.get('type')}")
            
        if metadata.get('shell_type') not in SpellParser.ALLOWED_SHELLS:
            raise ValueError(f"Invalid shell type: {metadata.get('shell_type')}")
            
        # Check entry point extension
        entry_point = Path(metadata['entry_point'])
        if entry_point.suffix not in SpellParser.ALLOWED_EXTENSIONS:
            raise ValueError(f"Invalid entry point file type: {metadata['entry_point']}")

    @staticmethod
    def _convert_yaml_to_metadata(config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert legacy spell.yaml format to standardized metadata."""
        return {
            'name': config.get('name'),
            'version': config.get('version', '1.0.0'),
            'description': config.get('description', ''),
            'type': config.get('type', 'bundled'),
            'shell_type': config.get('shell_type', 'python'),
            'entry_point': config.get('entry_point'),
            'parameters': config.get('parameters', {}),
            'dependencies': config.get('dependencies', {}),
            'created_at': '',  # Set during bundling
            'sigil_hash': None  # Calculated during bundling
        }

    @staticmethod
    def calculate_sigil_hash(spell_path: Path) -> str:
        """Calculate deterministic hash for spell sigil generation."""
        hasher = hashlib.sha256()
        
        try:
            # For bundled spells, hash all spell-related files
            with zipfile.ZipFile(spell_path, 'r') as zf:
                for file in sorted(zf.namelist()):
                    if file.endswith(('.py', '.sh', '.yaml', '.json')):
                        with zf.open(file) as f:
                            hasher.update(f.read())
        except zipfile.BadZipFile:
            # For macro spells, hash the entire content
            hasher.update(spell_path.read_bytes())
            
        return hasher.hexdigest()

    @staticmethod
    def execute_python_file(script_path: str, args=None):
        """Execute a Python script with optional arguments."""
        try:
            cmd = [sys.executable, script_path] + (args or [])
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def execute_bash_file(script_path: str):
        """Execute a bash script with platform-specific handling."""
        try:
            if sys.platform == 'win32':
                # On Windows, try Git Bash first, then WSL
                git_bash = r'C:\Program Files\Git\bin\bash.exe'
                if os.path.exists(git_bash):
                    cmd = [git_bash, script_path]
                else:
                    # Try WSL if Git Bash is not available
                    cmd = ['wsl', 'bash', script_path]
            else:
                # On Unix-like systems, use bash directly
                cmd = ['bash', script_path]
                
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to execute script: {e}")
            return False
        except FileNotFoundError as e:
            print("Error: bash not found. Please install Git Bash or WSL on Windows.")
            return False

    @staticmethod
    def execute_spell_file(spell_file, args=None):
        """Execute a spell file with sigil validation and optional arguments."""
        if args is None:
            args = []
        
        tome_path = os.path.join(SANCTUM_PATH, '.tome')
        spell_file_path = spell_file if '.tome' in spell_file else os.path.join(tome_path, spell_file)

        if not spell_file_path.endswith('.spell'):
            spell_file_path += '.spell'
        
        if not os.path.exists(spell_file_path):
            click.echo(f"Could not find {spell_file}.spell in .tome directory.")
            return
        
        print(f"Executing spell from: {spell_file_path}")
        try:
            # Extract and validate the spell bundle
            temp_dir, metadata = SpellParser.parse_bundle(Path(spell_file_path))
            try:
                # Execute the spell based on type and shell
                spell_type = metadata.get('type')
                shell_type = metadata.get('shell_type')
                entry_point = metadata['entry_point']
                
                print(f"Spell metadata:")
                print(f"- Type: {spell_type}")
                print(f"- Shell: {shell_type}")
                print(f"- Entry point: {entry_point}")
                print(f"- Temp dir: {temp_dir}")
                
                # Include spell name directory in possible paths
                spell_name = metadata['name']
                possible_paths = [
                    temp_dir / entry_point,
                    temp_dir / 'spell' / entry_point,
                    temp_dir / spell_name / entry_point,
                    temp_dir / spell_name / 'spell' / entry_point,
                ]
                
                script_path = None
                for path in possible_paths:
                    print(f"Checking path: {path}")
                    if path.exists():
                        script_path = path
                        print(f"Found script at: {script_path}")
                        break
                
                if not script_path:
                    print("Contents of temp directory:")
                    for path in temp_dir.rglob('*'):
                        print(f"  {path}")
                    click.echo(f"Error: Could not find entry point file: {entry_point}")
                    return False

                success = False
                if shell_type == 'python':
                    success = SpellParser.execute_python_file(str(script_path), args)
                elif shell_type == 'bash':
                    script_path.chmod(0o755)
                    success = SpellParser.execute_bash_file(str(script_path))
                elif shell_type == 'shell':
                    script_path.chmod(0o755)
                    success = SpellParser.execute_bash_file(str(script_path))
                
                if not success:
                    click.echo(f"Failed to execute {shell_type} spell: {script_path}")
                    return False
                
            finally:
                shutil.rmtree(temp_dir)
                
        except (zipfile.BadZipFile, KeyError) as e:
            click.echo(f"Error reading spell bundle: {e}")
            return False
        return True