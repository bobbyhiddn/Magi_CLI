import math
import random
import svgwrite

# Define runic sets by category
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
    "ᚑ", "ᚒ", "ᚓ", "ᚔ", "ᚕ"  # Complete Ogham set
]

# Combined sets for different purposes
ALL_RUNES = ELDER_FUTHARK + YOUNGER_FUTHARK + MEDIEVAL_RUNES + OGHAM
COMMON_RUNES = ELDER_FUTHARK + YOUNGER_FUTHARK  # Most historically common
MYSTICAL_RUNES = MEDIEVAL_RUNES + OGHAM  # More esoteric combinations

# Replace existing OGHAM_RUNES with new set
OGHAM_RUNES = OGHAM

def hash_to_params(hash_input: str) -> dict:
    """Convert hash to visualization parameters."""
    num_lines = int(hash_input[:2], 16) % 6 + 5  # 5-10 lines
    min_runes = int(hash_input[2:4], 16) % 2 + 1  # 1-2 minimum runes per line
    max_runes = int(hash_input[4:6], 16) % 2 + 2  # 2-3 maximum runes per line
    
    angles = []
    available_sectors = list(range(0, 360, 36))  # Divide circle into 10 sectors
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

def calculate_rune_position(center: int, radius: int, angle: float) -> tuple:
    """Calculate position for a rune based on radius and angle."""
    x = center + math.cos(math.radians(angle)) * radius
    y = center + math.sin(math.radians(angle)) * radius
    return (x, y)

def generate_outer_rim_with_advanced_runes(
    dwg, hash_input: str, center: int, radius: int, ring_width: int
) -> None:
    """Generate outer rim with mixed runes between boundary circles."""
    ring_width = 10  # Reduced from 20
    adjusted_radius = radius - (ring_width * 0.6)
    
    circumference = 2 * math.pi * adjusted_radius
    font_size = 5  # Small font size
    spacing_factor = 1.1
    num_runes = int(circumference / (font_size * spacing_factor))
    
    rune_indices = [int(hash_input[i:i+2], 16) % len(ALL_RUNES) 
                   for i in range(0, len(hash_input), 2)]
    rune_mappings = [{"rune": ALL_RUNES[idx], 
                      "rotation": (int(hash_input[i:i+2], 16) % 360)}
                     for i, idx in enumerate(rune_indices)]
    
    rune_mappings = (rune_mappings * (num_runes // len(rune_mappings) + 1))[:num_runes]
    
    angle_step = 360 / num_runes
    for i, rune_data in enumerate(rune_mappings):
        angle = i * angle_step
        x, y = calculate_rune_position(center, adjusted_radius, angle)
        
        dwg.add(dwg.text(
            rune_data["rune"],
            insert=(x, y),
            text_anchor="middle",
            alignment_baseline="middle",
            font_size=font_size,
            transform=f"rotate({rune_data['rotation'] + angle},{x},{y})"
        ))

def generate_center_rune(dwg, hash_input: str, center: int, size: int):
    """Generate a single centered rune based on hash input."""
    rune_index = int(hash_input[:2], 16) % len(ALL_RUNES)
    rune = ALL_RUNES[rune_index]
    
    dwg.add(dwg.text(
        rune,
        insert=(center, center + 8),
        text_anchor="middle",
        alignment_baseline="middle",
        font_size=70,
    ))

def generate_starburst_with_symbols(
    dwg, hash_input: str, center: int, params: dict, inner_radius: int, outer_radius: int
) -> None:
    """Generate starburst pattern with variable runes on each line."""
    center_clear_radius = inner_radius * 0.4  # Start point from center
    line_end_radius = inner_radius  # Extend lines exactly to inner circle
    
    for i, angle in enumerate(params['angles']):
        start_x, start_y = calculate_rune_position(center, center_clear_radius, angle)
        end_x, end_y = calculate_rune_position(center, line_end_radius, angle)
        
        dwg.add(dwg.line(
            start=(start_x, start_y),
            end=(end_x, end_y),
            stroke='black',
            stroke_width=2
        ))
        
        available_length = line_end_radius - center_clear_radius
        hash_segment = int(hash_input[i*2:i*2+2], 16)
        num_runes = params['min_runes'] + (hash_segment % (params['max_runes'] - params['min_runes'] + 1))
        segment_length = available_length / (num_runes + 1)
        
        for j in range(num_runes):
            radius = center_clear_radius + segment_length * (j + 1)
            if j == num_runes - 1:
                radius = min(radius, line_end_radius - 5)  # Smaller gap from circle
            x, y = calculate_rune_position(center, radius, angle)
            
            rune_idx = (int(hash_input[(i+j)%32:(i+j)%32+2], 16) % len(OGHAM_RUNES))
            rune = OGHAM_RUNES[rune_idx]
            
            dwg.add(dwg.text(
                rune,
                insert=(x, y),
                text_anchor="middle",
                alignment_baseline="middle",
                font_size=14,
                transform=f"rotate({angle},{x},{y})"
            ))

def generate_starburst_spell_svg(hash_input: str, output_path: str) -> None:
    """Generate a spell SVG with enhanced starburst sigil."""
    size = 256
    center = size // 2
    ring_width = 10  # Thinner rune ring
    outer_radius = center - 20
    inner_radius = outer_radius - ring_width
    
    dwg = svgwrite.Drawing(output_path, size=(size, size))
    dwg.add(dwg.rect(insert=(0, 0), size=(size, size), fill="white"))
    
    params = hash_to_params(hash_input)
    
    # First add the stone grey background between circles
    dwg.add(dwg.circle(
        center=(center, center),
        r=outer_radius,
        fill="#E0E0E0",  # Stone grey color
        stroke="none"
    ))
    dwg.add(dwg.circle(
        center=(center, center),
        r=inner_radius,
        fill="white",
        stroke="none"
    ))
    
    # Add the two boundary circles
    dwg.add(dwg.circle(
        center=(center, center),
        r=outer_radius,
        stroke="black",
        stroke_width=1,
        fill="none"
    ))
    dwg.add(dwg.circle(
        center=(center, center),
        r=inner_radius,
        stroke="black",
        stroke_width=1,
        fill="none"
    ))
    
    # Generate outer rim runes
    generate_outer_rim_with_advanced_runes(
        dwg, hash_input, center, outer_radius, ring_width
    )
    
    # Generate starburst pattern after circles are drawn
    generate_starburst_with_symbols(
        dwg, hash_input, center, params, inner_radius, inner_radius
    )
    
    # Add center rune last
    generate_center_rune(dwg, hash_input, center, size)
    
    try:
        dwg.save()
        print(f"Successfully saved sigil to {output_path}")
    except Exception as e:
        print(f"Error saving file: {e}")

def main():
    try:
        import os
        output_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(output_dir, "starburst_spell.svg")
        
        # Generate test hash
        hash_input = ''.join(random.choice('0123456789abcdef') for _ in range(32))
        # hash_input = "6fc5823870d352c97df905034adadf34"
        print(f"Using hash input: {hash_input}")
        generate_starburst_spell_svg(hash_input, output_path)
        
    except Exception as e:
        print(f"Error in main: {e}")

if __name__ == "__main__":
    main()