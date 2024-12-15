import yaml
import zipfile
import tempfile
import json
import shutil
import math
import svgwrite
from datetime import datetime
from pathlib import Path
from io import BytesIO
from typing import Optional, Dict, Any, Tuple, List, Union, Literal
import hashlib
from enum import Enum
import os
import click
from magi_cli.spells import SANCTUM_PATH
from magi_cli.loci.spellcraft.sigildry import Sigildry

class SpellType(str, Enum):
    BUNDLED = "bundled"
    SCRIPT = "script"
    MACRO = "macro"

class ShellType(str, Enum):
    PYTHON = "python"
    BASH = "bash"

class SpellBundle:
    """Manages the creation and packaging of spell bundles."""

    ELDER_FUTHARK = [
        "ᚠ", "ᚢ", "ᚦ", "ᚨ", "ᚱ", "ᚲ", "ᚷ", "ᚹ", "ᚺ", "ᚾ", "ᛁ", "ᛃ", "ᛇ", "ᛈ", "ᛉ", "ᛊ",
        "ᛏ", "ᛒ", "ᛖ", "ᛗ", "ᛚ", "ᛜ", "ᛞ", "ᛟ"
    ]
    
    YOUNGER_FUTHARK = [
        "ᚠ", "ᚢ", "ᚦ", "ᚬ", "ᚱ", "ᚴ", "ᚼ", "ᚾ", "ᛁ", "ᛅ", "ᛋ", "ᛏ", "ᛒ", "ᛘ", "ᛚ", "ᛦ"
    ]
    
    MEDIEVAL_RUNES = [
        "ᛆ", "ᛒ", "ᛍ", "ᛑ", "ᛂ", "ᛓ", "ᛄ", "ᚻ", "ᛌ", "ᛕ", "ᛖ", "ᛗ", "ᚿ", "ᚮ", "ᛔ", "ᛩ",
        "ᛪ", "ᚱ", "ᛌ", "ᛐ", "ᚢ", "ᚡ", "ᚥ", "ᛨ"
    ]
    
    OGHAM = [
        "ᚁ", "ᚂ", "ᚃ", "ᚄ", "ᚅ", "ᚆ", "ᚇ", "ᚈ", "ᚉ", "ᚊ", "ᚋ", "ᚌ", "ᚍ", "ᚎ", "ᚏ", "ᚐ",
        "ᚑ", "ᚒ", "ᚓ", "ᚔ", "ᚕ"
    ]
    
    ALL_RUNES = ELDER_FUTHARK + YOUNGER_FUTHARK + MEDIEVAL_RUNES + OGHAM

    # TODO: See if this can just be passed from spellcraft
    def __init__(self, path: Path):
        """Initialize SpellBundle with a path."""
        self.path = Path(path)
        self.spell_dir = self.path  # Maintain compatibility with previous code
        self.config: Optional[Dict[str, Any]] = None
        self.temp_dir: Optional[Path] = None
        self.tome_dir = Path(SANCTUM_PATH) / '.tome'
        self.tome_dir.mkdir(parents=True, exist_ok=True)

    def _generate_spell_sigil(self, config: Dict[str, Any], sigil_hash: Optional[str] = None) -> Tuple[str, Path]:
        """
        Generate a sigil for a spell bundle.
        
        Args:
            config (Dict[str, Any]): Spell configuration
            sigil_hash (Optional[str]): Predefined hash for sigil generation
        
        Returns:
            Tuple[str, Path]: Generated sigil hash and sigil file path
        """
        # Use provided hash or generate a new one
        if not sigil_hash:
            sigil_hash = Sigildry.generate_sigil_hash(
                spell_name=config['name'],
                description=config.get('description', ''),
                spell_type=config.get('type', 'generic'),
                version=config.get('version', '1.0.0'),
                entry_point=config.get('entry_point', ''),
                shell_type=config.get('shell_type', ''),
                spell_dir=self.spell_dir
            )
        
        # Generate sigil path
        sigil_path = self.spell_dir / f"{config['name']}_sigil.svg"
        
        # Generate sigil
        click.echo(click.style("» Manifesting sigil at:", fg="bright_blue") + 
                  click.style(f" {sigil_path}", fg="cyan"))
        Sigildry.generate_sigil_from_spell(self.spell_dir, sigil_hash, sigil_path)
        
        return sigil_hash, sigil_path

    def create(self, output_dir: Optional[Path] = None) -> Path:
        """
        Create a spell bundle from the spell directory.
        
        Args:
            output_dir (Optional[Path]): Optional directory to save the spell bundle.
                                         If not provided, uses the default .tome directory.
        
        Returns:
            Path: Path to the created spell bundle
        """
        destination_dir = output_dir or self.tome_dir
        return self.create_bundle(destination_dir)

    def create_bundle(self, destination_dir: Path) -> Path:
        """Create a spell bundle from a directory with sigil."""
        if not self.is_valid_spell_dir:
            raise ValueError(f"Invalid spell directory: {self.spell_dir}")
            
        # Verify configuration and assets
        config = self.load_config()
        self.verify_assets()
        
        # Generate sigil
        sigil_hash, sigil_path = self._generate_spell_sigil(config)
        
        # Update spell.yaml with the hash
        config['sigil_hash'] = sigil_hash
        yaml_path = self.spell_dir / 'spell' / 'spell.yaml'
        with open(yaml_path, 'w') as f:
            yaml.safe_dump(config, f, default_flow_style=False)
        
        # Create bundle path
        bundle_name = f"{config['name']}.spell"
        bundle_path = destination_dir / bundle_name
        
        # Create the zip bundle
        with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Create metadata
            metadata = {
                "name": config["name"],
                "description": config["description"],
                "created_at": datetime.now().isoformat(),
                "entry_point": config["entry_point"],
                "shell_type": config.get("shell_type", "python"),
                "type": config.get("type", "bundled"),
                "version": config.get("version", "1.0.0"),
                "sigil_hash": sigil_hash,
                "dependencies": config.get('dependencies', {'python': []})
            }
            
            # Add metadata
            zf.writestr('spell.json', json.dumps(metadata, indent=2))
            
            # Add all files preserving directory structure
            for file_path in self.spell_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.spell_dir)
                    zf.write(file_path, arcname)
        
        return bundle_path

    def extract_bundle(self, extract_dir: Optional[Path] = None) -> Tuple[Path, Dict[str, Any]]:
        """Extract a bundled spell and return the temp directory and metadata."""
        if not self.spell_dir.suffix == '.spell' or not zipfile.is_zipfile(self.spell_dir):
            raise ValueError(f"Not a valid spell bundle: {self.spell_dir}")
            
        if extract_dir is None:
            temp_dir = Path(tempfile.mkdtemp(prefix='magi_spell_'))
            extract_dir = temp_dir
            
        with zipfile.ZipFile(self.spell_dir) as zf:
            zf.extractall(extract_dir)
            with open(extract_dir / 'spell.json') as f:
                metadata = json.load(f)
            
        return extract_dir, metadata

    def cleanup(self):
        """Clean up temporary files."""
        if hasattr(self, 'temp_dir') and self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def load_config(self) -> Dict[str, Any]:
        """Load and validate the spell configuration."""
        config_path = self.spell_dir / 'spell' / 'spell.yaml'
        if not config_path.exists():
            raise ValueError(f"No spell.yaml found in {self.spell_dir}")
            
        with open(config_path) as f:
            config = yaml.safe_load(f)
            
        # Basic validation
        required_fields = ['name', 'version', 'description', 'type', 'entry_point']
        missing = [field for field in required_fields if field not in config]
        if missing:
            raise ValueError(f"Missing required fields in spell.yaml: {', '.join(missing)}")
            
        return config
    
    def verify_assets(self) -> bool:
        """Verify all required assets exist."""
        config = self.load_config()
        for asset in config.get('assets', []):
            asset_path = self.spell_dir / asset['path']
            if asset.get('required', False) and not asset_path.exists():
                raise ValueError(f"Required asset missing: {asset['path']}")
        return True
    
    def create(self, spell_name: str, nested_dir: Path, sigil_hash: Optional[str] = None) -> Path:
        """
        Create a spell bundle from a directory.
        
        Args:
            spell_name (str): Name of the spell
            nested_dir (Path): Directory containing spell files
            sigil_hash (Optional[str]): Optional predefined hash for sigil generation
        
        Returns:
            Path: Path to the created spell bundle
        """
        # Load configuration
        config_path = nested_dir / 'spell.yaml'
        if not config_path.exists():
            raise ValueError(f"No spell.yaml found in {nested_dir}")
        
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        # Ensure config has required fields
        config.setdefault('name', spell_name)
        
        # Generate sigil
        sigil_hash, sigil_path = self._generate_spell_sigil(config, sigil_hash)
        
        # Create bundle
        bundle_path = self.tome_dir / f"{spell_name}.spell"
        
        with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add all files from spell directory first
            print("- Adding files to bundle:")
            for file_path in nested_dir.rglob('*'):
                if file_path.is_file():
                    try:
                        arcname = file_path.relative_to(nested_dir)
                        print(f"  Adding: {arcname}")
                        # Read file content and add to zip to avoid file locking
                        content = file_path.read_bytes()
                        zf.writestr(str(arcname), content)
                    except Exception as e:
                        print(f"Warning: Could not add file {file_path}: {e}")
            
            # Generate sigil ONCE and add to bundle
            sigil_path = nested_dir / f"{spell_name}_sigil.svg"
            print(f"- Generating sigil at: {sigil_path}")
            Sigildry.generate_sigil_from_spell(nested_dir, sigil_hash, sigil_path)
            
            # Add sigil to bundle
            sigil_name = f"{spell_name}_sigil.svg"
            with open(sigil_path, 'rb') as sigil_file:
                zf.writestr(sigil_name, sigil_file.read())
            
            # Store the hash in metadata and add metadata last
            metadata = {
                "name": config['name'],
                "description": config.get('description', ''),
                "created_at": datetime.now().isoformat(),
                "entry_point": config.get('entry_point', ''),
                "shell_type": config.get('shell_type', 'python'),
                "type": config.get('type', 'generic'),
                "version": config.get('version', '1.0.0'),
                "sigil_hash": sigil_hash,
                "dependencies": config.get('dependencies', {'python': []})
            }
            zf.writestr('spell.json', json.dumps(metadata, indent=2))
        
        return bundle_path

    @classmethod
    def create_spell_bundle(cls, 
                          spell_name: str, 
                          spell_type: Union[SpellType, str], 
                          shell_type: Union[ShellType, str],
                          entry_point: str, 
                          description: str, 
                          spell_dir: Path,
                          verify_structure: bool = True) -> Path:
        # Normalize types
        if isinstance(spell_type, str):
            spell_type = getattr(SpellType, spell_type.upper(), SpellType.SCRIPT)
        if isinstance(shell_type, str):
            shell_type = getattr(ShellType, shell_type.upper(), ShellType.PYTHON)
            
        # Create metadata
        metadata = {
            "name": spell_name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "entry_point": entry_point,
            "shell_type": shell_type,
            "type": spell_type,
            "version": "1.0.0",
            "dependencies": {'python': []}
        }
        
        # Create bundle path
        bundle_path = Path(SANCTUM_PATH) / '.tome' / f'{spell_name}.spell'

        try:
            # Create zip bundle
            with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add all files from spell directory first
                print("- Adding files to bundle:")
                for file_path in spell_dir.rglob('*'):
                    if file_path.is_file():
                        try:
                            arcname = file_path.relative_to(spell_dir)
                            print(f"  Adding: {arcname}")
                            # Read file content and add to zip to avoid file locking
                            content = file_path.read_bytes()
                            zf.writestr(str(arcname), content)
                        except Exception as e:
                            print(f"Warning: Could not add file {file_path}: {e}")
                
                # Generate sigil ONCE and add to bundle
                sigil_path = spell_dir / f"{spell_name}_sigil.svg"
                print(f"- Generating sigil at: {sigil_path}")
                sigil_hash = Sigildry.generate_sigil_hash(
                    spell_name=spell_name,
                    description=description,
                    spell_type=spell_type,
                    version="1.0.0",
                    entry_point=entry_point,
                    shell_type=shell_type,
                    spell_dir=spell_dir
                )
                Sigildry.generate_sigil_from_spell(spell_dir, sigil_hash, sigil_path)
                
                # Add sigil to bundle
                sigil_name = f"{spell_name}_sigil.svg"
                with open(sigil_path, 'rb') as sigil_file:
                    zf.writestr(sigil_name, sigil_file.read())
                
                # Store the hash in metadata and add metadata last
                metadata['sigil_hash'] = sigil_hash
                zf.writestr('spell.json', json.dumps(metadata, indent=2))

                # Update spell.yaml with the hash
                yaml_path = spell_dir / 'spell' / 'spell.yaml'
                if yaml_path.exists():
                    with open(yaml_path) as f:
                        yaml_config = yaml.safe_load(f)
                    yaml_config['sigil_hash'] = sigil_hash
                    with open(yaml_path, 'w') as f:
                        yaml.safe_dump(yaml_config, f, default_flow_style=False)

        except Exception as e:
            if bundle_path.exists():
                bundle_path.unlink()  # Clean up failed bundle
            raise

        print(f"Bundle created at: {bundle_path}")
        return bundle_path

    @classmethod
    def _verify_spell_directory(cls, spell_dir: Path):
        """
        Verify the structure of the spell directory.
        
        Checks:
        - spell.yaml exists
        - Validates basic spell configuration
        """
        # Check for spell.yaml
        spell_yaml = spell_dir / 'spell.yaml'
        if not spell_yaml.exists():
            raise ValueError(f"Missing spell.yaml in {spell_dir}")
        
        # Optional: Add more validation checks here
        # For example, check required keys in spell.yaml, validate entry point, etc.

    @property
    def is_valid_spell_dir(self) -> bool:
        """Check if the directory contains a valid spell.yaml."""
        config_path = self.spell_dir / 'spell' / 'spell.yaml'
        return config_path.exists()