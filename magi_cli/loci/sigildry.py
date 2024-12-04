#!/usr/bin/env python3

import os
import random
import math
import svgwrite
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Union
import json
import yaml
import tempfile
import zipfile
from enum import Enum

from magi_cli.spells import SANCTUM_PATH

class SpellType(Enum):
    SCRIPT = 'script'
    BUNDLE = 'bundle'

class ShellType(Enum):
    PYTHON = 'python'
    BASH = 'bash'

class Sigildry:
    """
    Handles sigil (cryptographic signature) generation, verification, 
    and management for Magi spells.
    """
    
    # Rune sets from SpellBundle
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
        
        # Generate random color
        circle_color = f"#{hash_input[6:12]}"

        # Add stone grey background between circles
        dwg.add(dwg.circle(center=(center, center), r=outer_radius, fill="#E0E0E0", stroke="none"))
        dwg.add(dwg.circle(center=(center, center), r=inner_radius, fill=circle_color, stroke="none"))
        
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

    @staticmethod
    def generate_sigil_hash(
        spell_name: str,
        description: str,
        spell_type: Union[SpellType, str],
        version: str,
        entry_point: str,
        shell_type: Union[ShellType, str],
        spell_dir: Path
    ) -> str:
        """
        Generate a hash for a spell's sigil.
        
        Args:
            spell_name (str): Name of the spell
            description (str): Description of the spell
            spell_type (Union[SpellType, str]): Type of spell
            version (str): Version of the spell
            entry_point (str): Entry point file path
            shell_type (Union[ShellType, str]): Shell type for the spell
            spell_dir (Path): Directory containing spell files
            
        Returns:
            str: Generated hash for the sigil
        """
        # Normalize types
        if isinstance(spell_type, str):
            spell_type = getattr(SpellType, spell_type.upper(), SpellType.SCRIPT)
        if isinstance(shell_type, str):
            shell_type = getattr(ShellType, shell_type.upper(), ShellType.PYTHON)

        # Create hasher
        hasher = hashlib.sha256()

        # Add metadata to hash in a consistent order
        metadata_str = f"{spell_name}\n{description}\n{spell_type}\n{version}\n{entry_point}\n{shell_type}"
        hasher.update(metadata_str.encode())

        # Add file contents to hash in a consistent order
        for file_path in sorted(spell_dir.rglob('*')):
            if file_path.is_file():
                # Skip metadata and sigil files
                if file_path.name in ['spell.json', 'spell.yaml'] or file_path.name.endswith('_sigil.svg'):
                    continue
                    
                # Get relative path for consistent hashing
                rel_path = file_path.relative_to(spell_dir)
                hasher.update(str(rel_path).encode())
                
                # Add file contents
                with open(file_path, 'rb') as f:
                    while chunk := f.read(8192):
                        hasher.update(chunk)

        return hasher.hexdigest()

    @staticmethod
    def generate_sigil_from_spell(
        spell_path: Path, 
        sigil_hash: Optional[str] = None,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Generate sigil for a given spell.
        
        Args:
            spell_path (Path): Path to the spell
            sigil_hash (Optional[str]): Predefined hash for sigil generation
            output_path (Optional[Path]): Custom output path for sigil
        
        Returns:
            Path: Path to the generated sigil SVG
        """
        # This method requires metadata from the spell
        # Implement a generic way to extract spell metadata without SpellBundle
        try:
            # Placeholder for spell metadata extraction
            # You might want to implement a generic metadata extraction method
            metadata = {
                'name': spell_path.stem,
                'description': f'Spell at {spell_path}',
                'type': 'generic'
            }
            
            # Generate hash if not provided
            if sigil_hash is None:
                sigil_hash = Sigildry.generate_sigil_hash(
                    metadata['name'], 
                    metadata.get('description', ''), 
                    metadata.get('type', 'unknown')
                )
            
            # Determine sigil path
            if output_path is None:
                output_path = spell_path.parent / f"{metadata['name']}_sigil.svg"
            
            # Generate sigil
            sigildry = Sigildry()
            sigildry.generate_sigil(sigil_hash, output_path)
            
            return output_path
        
        except Exception as e:
            print(f"Error generating sigil: {e}")
            return None

    @staticmethod
    def verify_sigil(
        spell_path: Path, 
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Verify the integrity of a spell using its sigil.
        
        Args:
            spell_path (Path): Path to the spell bundle
            verbose (bool, optional): Enable detailed logging. Defaults to False.
        
        Returns:
            Dict[str, Any]: Verification details with 'verified' key
        """
        try:
            # Unpack the spell bundle
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir_path = Path(temp_dir)
                
                # Extract spell contents
                with zipfile.ZipFile(spell_path, 'r') as zip_ref:
                    # Extract all files except spell.json and sigil
                    for file_info in zip_ref.filelist:
                        if file_info.filename not in ['spell.json', f"{Path(spell_path).stem}_sigil.svg"]:
                            zip_ref.extract(file_info, temp_dir_path)
                    
                    # Load metadata from spell.json (primary source)
                    metadata = {}
                    with zip_ref.open('spell.json') as f:
                        metadata = json.load(f)
                
                # If no metadata found at all
                if not metadata:
                    if verbose:
                        print(f"No metadata found in {spell_path}")
                    return {
                        'verified': False,
                        'error': 'No metadata found',
                        'metadata': {}
                    }
                
                # Get stored hash from metadata
                stored_hash = metadata.get('sigil_hash')
                if not stored_hash:
                    if verbose:
                        print("No stored hash found in metadata")
                    return {
                        'verified': False,
                        'error': 'No stored hash found',
                        'metadata': metadata
                    }
                
                # Calculate current hash using the same process as bundle creation
                current_hash = Sigildry.generate_sigil_hash(
                    spell_name=metadata.get('name', ''),
                    description=metadata.get('description', ''),
                    spell_type=metadata.get('type', 'generic'),
                    version=metadata.get('version', '1.0.0'),
                    entry_point=metadata.get('entry_point', ''),
                    shell_type=metadata.get('shell_type', ''),
                    spell_dir=temp_dir_path
                )
                
                if verbose:
                    print(f"Verifying sigil hash:")
                    print(f"  Stored:  {stored_hash}")
                    print(f"  Current: {current_hash}")
                
                if current_hash != stored_hash:
                    print(f"Sigil hash mismatch! Spell has been tampered with.\nStored: {stored_hash}\nCurrent: {current_hash}")
                    import sys
                    sys.exit(1)

                return {
                    'verified': True,
                    'verification_status': 'Verified',
                    'metadata': metadata,
                    'current_hash': current_hash,
                    'stored_hash': stored_hash
                }

        except Exception as e:
            if verbose:
                print(f"Sigil verification failed: {e}")
            return {
                'verified': False,
                'error': str(e),
                'verification_status': 'Verification Error',
                'metadata': {}
            }

    @staticmethod
    def check_spell_conflict(
        spell_path: Path, 
        tome_path: Optional[Path] = None,
        allow_overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Check for potential spell conflicts.
        
        Args:
            spell_path (Path): Path to the new spell
            tome_path (Optional[Path]): Path to the spell tome
            allow_overwrite (bool): Whether to allow overwriting existing spells
        
        Returns:
            Dict containing conflict information
        """
        tome_path = tome_path or Path(SANCTUM_PATH) / '.tome'
        
        # Placeholder for spell metadata extraction
        metadata = {
            'name': spell_path.stem,
            'description': f'Spell at {spell_path}',
            'type': 'generic'
        }
        spell_name = metadata['name']
        
        # Check for existing spell with same name
        existing_spell_path = tome_path / f"{spell_name}.spell"
        
        if existing_spell_path.exists():
            # Verify sigils
            new_verification = Sigildry.verify_sigil(spell_path)
            existing_verification = Sigildry.verify_sigil(existing_spell_path)
            
            return {
                'conflict': True,
                'spell_name': spell_name,
                'new_spell_details': new_verification,
                'existing_spell_details': existing_verification,
                'allow_overwrite': allow_overwrite
            }
        
        return {
            'conflict': False,
            'spell_name': spell_name,
            'metadata': metadata
        }
