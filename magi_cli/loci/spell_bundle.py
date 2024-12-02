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
from magi_cli.spells import SANCTUM_PATH

class SpellType(str, Enum):
    BUNDLED = "bundled"
    SCRIPT = "script"
    MACRO = "macro"

class ShellType(str, Enum):
    PYTHON = "python"
    BASH = "bash"

class SpellBundle:
    """Handles spell bundle creation, validation, and management."""
    
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

    def __init__(self, path: Path):
        self.path = Path(path)
        self.config: Optional[Dict[str, Any]] = None
        self.temp_dir: Optional[Path] = None

    @classmethod
    def create_spell_bundle(cls, 
                          spell_name: str, 
                          spell_type: Union[SpellType, str], 
                          shell_type: Union[ShellType, str],
                          entry_point: str, 
                          description: str, 
                          spell_dir: Path,
                          verify_structure: bool = True) -> Path:
        """Creates a spell bundle with proper metadata and nested directory structure."""
        tome_dir = Path(SANCTUM_PATH) / '.tome'
        tome_dir.mkdir(parents=True, exist_ok=True)
        bundle_path = tome_dir / f"{spell_name}.spell"

        print(f"Creating spell bundle:")
        print(f"- Name: {spell_name}")
        print(f"- Type: {spell_type}")
        print(f"- Entry point: {entry_point}")
        print(f"- Base dir: {spell_dir}")
        
        # Create nested spell directory structure if needed
        nested_dir = spell_dir / 'spell'  # Use consistent 'spell' directory
        nested_dir.mkdir(parents=True, exist_ok=True)
        print(f"- Created nested dir: {nested_dir}")

        # Handle entry point file
        entry_path = spell_dir / entry_point
        target_path = nested_dir / Path(entry_point).name
        print(f"- Moving from: {entry_path}")
        print(f"- Moving to: {target_path}")
        
        try:
            if entry_path.exists():
                if not target_path.parent.exists():
                    target_path.parent.mkdir(parents=True)
                # Use read and write instead of copy to avoid file locking
                content = entry_path.read_bytes()
                target_path.write_bytes(content)
                if shell_type == ShellType.BASH:
                    target_path.chmod(0o755)
                    print("- Made script executable")
        except Exception as e:
            print(f"Warning: Could not copy entry point: {e}")

        # Create spell.yaml in nested directory
        yaml_config = {
            'name': spell_name,
            'description': description,
            'version': '1.0.0',
            'type': spell_type,
            'shell_type': shell_type,
            'entry_point': Path(entry_point).name,  # Use just the filename
            'requires': []  # Initialize empty requires list
        }
        
        # Load existing requires if present
        existing_yaml = nested_dir / 'spell.yaml'
        if existing_yaml.exists():
            with open(existing_yaml) as f:
                existing_config = yaml.safe_load(f)
                if 'requires' in existing_config:
                    yaml_config['requires'] = existing_config['requires']
        
        print("- Writing spell.yaml")
        yaml_path = nested_dir / 'spell.yaml'
        with open(yaml_path, 'w') as f:
            yaml.dump(yaml_config, f, default_flow_style=False)

        # Generate sigil hash
        sigil_hash = hashlib.md5(f"{spell_name}_{description}_{spell_type}".encode()).hexdigest()
        print(f"- Generated sigil hash: {sigil_hash}")

        # Generate metadata with standardized dependencies format
        metadata = {
            "name": spell_name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "entry_point": Path(entry_point).name,  # Use just the filename
            "shell_type": shell_type,
            "type": spell_type,
            "version": "1.0.0",
            "sigil_hash": sigil_hash,
            "dependencies": {"python": yaml_config['requires']}  # Use standardized format
        }

        print("- Creating bundle...")
        # Create the bundle
        try:
            with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add metadata
                zf.writestr('spell.json', json.dumps(metadata, indent=2))
                
                # Generate and add sigil
                sigil_path = nested_dir / f"{spell_name}_sigil.svg"
                print(f"- Generating sigil at: {sigil_path}")
                bundle = cls(spell_dir)
                bundle.generate_sigil(sigil_hash, str(sigil_path))
                
                # Add all files from spell directory
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
        except Exception as e:
            if bundle_path.exists():
                bundle_path.unlink()  # Clean up failed bundle
            raise

        print(f"Bundle created at: {bundle_path}")
        return bundle_path

    def extract_bundle(self, extract_dir: Optional[Path] = None) -> Tuple[Path, Dict[str, Any]]:
        """Extract a bundled spell and return the temp directory and metadata."""
        if not self.path.suffix == '.spell' or not zipfile.is_zipfile(self.path):
            raise ValueError(f"Not a valid spell bundle: {self.path}")
            
        if extract_dir is None:
            self.temp_dir = Path(tempfile.mkdtemp(prefix='magi_spell_'))
            extract_dir = self.temp_dir
            
        with zipfile.ZipFile(self.path) as zf:
            zf.extractall(extract_dir)
            with open(extract_dir / 'spell.json') as f:
                metadata = json.load(f)
            
        return extract_dir, metadata

    def cleanup(self):
        """Clean up temporary files."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def load_config(self) -> Dict[str, Any]:
        """Load and validate the spell configuration."""
        config_path = self.path / 'spell' / 'spell.yaml'
        if not config_path.exists():
            raise ValueError(f"No spell.yaml found in {self.path}")
            
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
            asset_path = self.path / asset['path']
            if asset.get('required', False) and not asset_path.exists():
                raise ValueError(f"Required asset missing: {asset['path']}")
        return True
    
    def _calculate_bundle_hash(self) -> str:
        """Calculate a hash of the bundle contents."""
        config = self.load_config()
        # Create a hash of the name and version
        hash_input = f"{config['name']}_{config['version']}".encode('utf-8')
        # Generate a hex hash string
        return hashlib.md5(hash_input).hexdigest()
    
    def _hash_to_params(self, hash_input: str) -> dict:
        """Convert hash to visualization parameters."""
        num_lines = int(hash_input[:2], 16) % 6 + 5
        min_runes = int(hash_input[2:4], 16) % 2 + 1
        max_runes = int(hash_input[4:6], 16) % 2 + 2
        
        angles = []
        available_sectors = list(range(0, 360, 36))
        for i in range(num_lines):
            hash_segment = int(hash_input[i*2:i*2+2], 16)
            sector_index = hash_segment % len(available_sectors)
            base_angle = available_sectors.pop(sector_index)
            jitter = int(hash_input[i*2+2:i*2+4], 16) % 20 - 10
            angles.append(base_angle + jitter)
        
        return {
            'num_lines': num_lines,
            'min_runes': min_runes,
            'max_runes': max_runes,
            'angles': angles
        }

    def _calculate_rune_position(self, center: int, radius: int, angle: float) -> tuple:
        """Calculate position for a rune based on radius and angle."""
        x = center + math.cos(math.radians(angle)) * radius
        y = center + math.sin(math.radians(angle)) * radius
        return (x, y)

    def generate_sigil(self, hash_input: str, output_path: Path, size: int = 256) -> None:
        """Generate a spell sigil SVG with enhanced starburst pattern."""
        center = size // 2
        ring_width = 10
        outer_radius = center - 20
        inner_radius = outer_radius - ring_width
        
        dwg = svgwrite.Drawing(output_path, size=(size, size))
        dwg.add(dwg.rect(insert=(0, 0), size=(size, size), fill="white"))
        
        params = self._hash_to_params(hash_input)
        
        # Add stone grey background between circles
        dwg.add(dwg.circle(center=(center, center), r=outer_radius, fill="#E0E0E0", stroke="none"))
        dwg.add(dwg.circle(center=(center, center), r=inner_radius, fill="white", stroke="none"))
        
        # Add boundary circles
        for radius in (outer_radius, inner_radius):
            dwg.add(dwg.circle(
                center=(center, center),
                r=radius,
                stroke="black",
                stroke_width=1,
                fill="none"
            ))
        
        # Generate outer rim runes
        self._generate_outer_rim(dwg, hash_input, center, outer_radius, ring_width)
        
        # Generate starburst pattern
        self._generate_starburst(dwg, hash_input, center, params, inner_radius)
        
        # Add center rune
        self._generate_center_rune(dwg, hash_input, center, size)
        
        dwg.save()

    def _generate_outer_rim(self, dwg, hash_input: str, center: int, radius: int, ring_width: int) -> None:
        """Generate outer rim with mixed runes."""
        adjusted_radius = radius - (ring_width * 0.6)
        circumference = 2 * math.pi * adjusted_radius
        font_size = 5
        spacing_factor = 1.1
        num_runes = int(circumference / (font_size * spacing_factor))
        
        rune_indices = [int(hash_input[i:i+2], 16) % len(self.ALL_RUNES) 
                       for i in range(0, len(hash_input), 2)]
        rune_mappings = [{"rune": self.ALL_RUNES[idx], 
                         "rotation": (int(hash_input[i:i+2], 16) % 360)}
                        for i, idx in enumerate(rune_indices)]
        
        rune_mappings = (rune_mappings * (num_runes // len(rune_mappings) + 1))[:num_runes]
        
        angle_step = 360 / num_runes
        for i, rune_data in enumerate(rune_mappings):
            angle = i * angle_step
            x, y = self._calculate_rune_position(center, adjusted_radius, angle)
            dwg.add(dwg.text(
                rune_data["rune"],
                insert=(x, y),
                text_anchor="middle",
                alignment_baseline="middle",
                font_size=5,
                transform=f"rotate({rune_data['rotation'] + angle},{x},{y})"
            ))

    def _generate_starburst(self, dwg, hash_input: str, center: int, params: dict, inner_radius: int) -> None:
        """Generate starburst pattern with variable runes on each line."""
        center_clear_radius = inner_radius * 0.4
        line_end_radius = inner_radius
        
        for i, angle in enumerate(params['angles']):
            start_x, start_y = self._calculate_rune_position(center, center_clear_radius, angle)
            end_x, end_y = self._calculate_rune_position(center, line_end_radius, angle)
            
            dwg.add(dwg.line(start=(start_x, start_y), end=(end_x, end_y),
                            stroke='black', stroke_width=2))
            
            self._add_runes_to_line(dwg, hash_input, center, i, angle, params,
                                  center_clear_radius, line_end_radius)

    def _add_runes_to_line(self, dwg, hash_input, center, i, angle, params,
                          start_radius, end_radius):
        """Add runes along a starburst line."""
        available_length = end_radius - start_radius
        hash_segment = int(hash_input[i*2:i*2+2], 16)
        num_runes = params['min_runes'] + (hash_segment % (params['max_runes'] - params['min_runes'] + 1))
        segment_length = available_length / (num_runes + 1)
        
        for j in range(num_runes):
            radius = start_radius + segment_length * (j + 1)
            if j == num_runes - 1:
                radius = min(radius, end_radius - 5)
            x, y = self._calculate_rune_position(center, radius, angle)
            
            rune_idx = (int(hash_input[(i+j)%32:(i+j)%32+2], 16) % len(self.OGHAM))
            rune = self.OGHAM[rune_idx]
            
            dwg.add(dwg.text(
                rune,
                insert=(x, y),
                text_anchor="middle",
                alignment_baseline="middle",
                font_size=14,
                transform=f"rotate({angle},{x},{y})"
            ))

    def _generate_center_rune(self, dwg, hash_input: str, center: int, size: int):
        """Generate a single centered rune."""
        rune_index = int(hash_input[:2], 16) % len(self.ALL_RUNES)
        rune = self.ALL_RUNES[rune_index]
        
        dwg.add(dwg.text(
            rune,
            insert=(center, center + 8),
            text_anchor="middle",
            alignment_baseline="middle",
            font_size=70,
        ))

    @property
    def is_valid_spell_dir(self) -> bool:
        """Check if the directory contains a valid spell.yaml."""
        config_path = self.path / 'spell' / 'spell.yaml'
        return config_path.exists()

    def create_bundle(self, output_dir: Path) -> Path:
        """Create a spell bundle from a directory with sigil."""
        if not self.is_valid_spell_dir:
            raise ValueError(f"Invalid spell directory: {self.path}")
            
        # Verify configuration and assets
        config = self.load_config()
        self.verify_assets()
        
        # Create bundle name
        bundle_name = f"{config['name']}.spell"
        bundle_path = output_dir / bundle_name
        
        # Generate sigil
        sigil_hash = self._calculate_bundle_hash()
        
        # Create temporary file for SVG
        with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as temp_svg:
            # Generate sigil to temporary file
            self.generate_sigil(sigil_hash, temp_svg.name)
            
            # Create metadata from config
            metadata = {
                "name": config["name"],
                "description": config["description"],
                "created_at": datetime.now().isoformat(),
                "entry_point": config["entry_point"],  # Use entry_point consistently
                "shell_type": config.get("shell_type", "python"),
                "type": config.get("type", "bundled"),
                "version": config.get("version", "1.0.0"),
                "sigil_hash": sigil_hash,
                "dependencies": config.get('dependencies', {'python': []})  # Use dependencies from config
            }
            
            # Create the zip bundle
            with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add metadata first
                zf.writestr('spell.json', json.dumps(metadata, indent=2))
                
                # Add sigil from temporary file
                zf.write(temp_svg.name, f"{config['name']}_sigil.svg")
                
                # Add all files preserving directory structure
                for file_path in self.path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(self.path)
                        zf.write(file_path, arcname)
        
        # Clean up temporary file
        Path(temp_svg.name).unlink()
                        
        return bundle_path