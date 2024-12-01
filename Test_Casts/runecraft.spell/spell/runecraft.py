import os
import sys
import click
import base64
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
from jinja2 import Template
import requests
import subprocess
from io import BytesIO
from openai import OpenAI
from magi_cli.spells import SANCTUM_PATH

__requires__ = ['click', 'requests', 'Pillow', 'openai', 'PyQt5', 'jinja2']

def load_assets():
    """Load required assets for the rune generation."""
    # Get absolute path of current script
    current_script = Path(__file__).resolve()
    spell_root = current_script.parent.parent
    
    # Define asset paths relative to spell root
    rune_template = spell_root / 'artifacts' / 'rune_template.j2'
    default_rune = spell_root / 'artifacts' / 'default_rune.png'
    
    # Debug info
    # print(f"Looking for assets in: {spell_root}")
    # print(f"Template path: {rune_template}")
    # print(f"Default rune path: {default_rune}")
    
    if not (rune_template.exists() and default_rune.exists()):
        raise FileNotFoundError(
            f"Required assets not found:\n"
            f"Template exists: {rune_template.exists()}\n"
            f"Default rune exists: {default_rune.exists()}"
        )
        
    return {
        'template': rune_template.read_text(),
        'default_rune': default_rune
    }

def generate_rune(script_path: Path, output_path: Path, assets: dict):
    """Generate a magical rune that executes the script when activated."""
    # Read and encode script
    script_content = script_path.read_text()
    encoded_script = base64.b64encode(script_content.encode()).decode()
    
    # Generate script template
    template = Template(assets['template'])
    script_wrapper = template.render(
        script_content=encoded_script,
        script_path=str(script_path)
    )
    
    # Create rune image
    base_image = Image.open(assets['default_rune'])
    draw = ImageDraw.Draw(base_image)
    
    # Add script hash as visual elements
    script_hash = hash(script_content) & 0xFFFFFF  # Get last 6 hex digits
    r = (script_hash >> 16) & 255
    g = (script_hash >> 8) & 255
    b = script_hash & 255
    
    # Apply magical sigils
    draw.ellipse([20, 20, 80, 80], fill=(r, g, b, 128))
    
    # Save rune with embedded script
    base_image.save(output_path, format='PNG')
    
    # Save script wrapper
    wrapper_path = output_path.with_suffix('.rune.py')
    wrapper_path.write_text(script_wrapper)

def generate_image(prompt, default_image_path):
    """Generate rune image using DALL-E or fall back to default."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        click.echo("No OPENAI_API_KEY found. Using default rune image.")
        return Image.open(default_image_path)

    client = OpenAI(api_key=api_key)
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024",
            response_format="url"
        )
        image_url = response.data[0].url
        image_data = requests.get(image_url).content
        return Image.open(BytesIO(image_data))
    except Exception as e:
        click.echo(f"Failed to generate image: {e}. Using default rune image.")
        return Image.open(default_image_path)

def create_circular_mask(image):
    """Create a circular mask for the rune image."""
    width, height = image.size
    mask = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, width, height), fill=255)
    return mask

def process_rune_image(image):
    """Process image into circular rune format."""
    # Create circular mask
    width, height = image.size
    mask = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, width, height), fill=255)
    
    # Apply mask and fit image
    circular_image = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    circular_image.putalpha(mask)
    
    # Convert to RGBA for transparency
    return circular_image.convert('RGBA')

def create_rune_window(image_path, script_path, output_path, template):
    """Create a GUI window for the rune using the template."""
    extension = script_path.suffix
    # Windows-specific command mapping with proper escaping
    command_map = {
        '.sh': 'bash',  # Git Bash with forward slashes
        '.py': 'python',  # Python path escaped
        '.spell': 'cast'
    }
    command = command_map.get(extension, str(sys.executable).replace('\\', '\\\\'))
    
    # Create safe path strings
    image_path_str = str(image_path).replace('\\', '\\\\')
    script_path_str = str(script_path).replace('\\', '\\\\')
    
    with open(output_path, 'w') as f:
        f.write(Template(template).render(
            image_path=image_path_str,
            command=command,
            script_path=script_path_str
        ))

def get_success_message(message: str) -> str:
    """Get a success message with appropriate emoji based on environment."""
    try:
        "✨".encode(sys.stdout.encoding)
        return f"✨ {message}"
    except UnicodeEncodeError:
        return f"* {message}"

@click.command()
@click.argument('script_path', type=click.Path(exists=True))
@click.option('--output', '-o', default=None)
def runecraft(script_path, output):
    """Generate an enchanted rune to execute a script."""
    try:
        assets = load_assets()
        script_path = Path(script_path).resolve()
        
        # Create runes directory
        runes_dir = Path(SANCTUM_PATH) / '.runes' / script_path.stem
        runes_dir.mkdir(parents=True, exist_ok=True)
        
        # Set output paths without duplicate extensions
        if output is None:
            output = runes_dir / f"{script_path.stem}.png"
            

        print("Gathering the mana...")
        print("Applying the enchantment...")
        print("Engaging the arcane energies...")
        print("Engraving the rune from aether to stone...")
        print("(This may take up to 15 seconds)")

        prompt = "Rune magic, arcane symbol, runework, gemstone, central sigil, ancient arcane language, modern pixel video game style icon, engraved in the aether and onto stone, magical energy"
        image = generate_image(prompt, assets['default_rune'])
        processed_image = process_rune_image(image)
        processed_image.save(output)
        
        # Create GUI script with correct extension
        gui_path = runes_dir / f"{script_path.stem}.py"
        create_rune_window(output, script_path, gui_path, assets['template'])
        
        click.echo(get_success_message(f"Rune crafted successfully: {output}"))
        subprocess.Popen([sys.executable, str(gui_path)], start_new_session=True)
        
    except Exception as e:
        click.echo(f"Error crafting rune: {str(e)}", err=True)
        sys.exit(1)

alias = "rc"

if __name__ == '__main__':
    runecraft()