import click
import os
import json
import zipfile
import tempfile
import shutil
import yaml
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, Any
from magi_cli.spells import SANCTUM_PATH

SUPPORTED_SHELLS = {
    'bash': {
        'extension': '.sh',
        'description': 'Unix/Linux bash shell',
        'shebang': '#!/bin/bash'
    },
    'batch': {
        'extension': '.bat',
        'description': 'Windows batch shell',
        'shebang': '@echo off'
    },
    'python': {
        'extension': '.py',
        'description': 'Python script',
        'shebang': '#!/usr/bin/env python3'
    }
}

def create_spell_metadata(name: str, description: str, shell_type: str, spell_alias: str = None) -> Dict[str, Any]:
    """Creates standardized metadata for a spell bundle."""
    if shell_type not in SUPPORTED_SHELLS:
        raise ValueError(f"Unsupported shell type: {shell_type}")
    
    return {
        'name': name,
        'description': description,
        'spell_alias': spell_alias,
        'version': '1.0.0',
        'created_at': datetime.now(UTC).isoformat(),
        'shell_type': shell_type,
        'parameters': {},
        'dependencies': [],
        'runtime': {
            'container': None
        }
    }

def create_spell_bundle_from_yaml(yaml_path: Path, spell_name: str) -> Path:
    """Creates a spell bundle from a YAML specification file."""
    with open(yaml_path, 'r') as f:
        spec = yaml.safe_load(f)
    
    temp_dir = Path(tempfile.mkdtemp(prefix='magi_spell_'))
    try:
        # Create metadata
        metadata = create_spell_metadata(
            name=spec.get('name', spell_name),
            description=spec.get('description', ''),
            shell_type=spec.get('shell_type', 'bash'),
            spell_alias=spec.get('spell_alias')
        )
        
        # Add parameters and dependencies
        metadata['parameters'] = spec.get('parameters', {})
        metadata['dependencies'] = spec.get('dependencies', [])
        
        # Create script from commands
        script_content = generate_shell_script(spec['commands'], metadata['shell_type'], metadata['parameters'])
        
        extension = SUPPORTED_SHELLS[metadata['shell_type']]['extension']
        script_path = temp_dir / f"{spell_name}{extension}"
        script_path.write_text(script_content)
        
        # Save metadata
        metadata_path = temp_dir / 'spell.json'
        metadata_path.write_text(json.dumps(metadata, indent=2))
        
        # Create bundle
        return create_spell_bundle_from_directory(temp_dir, spell_name, metadata['description'])
    finally:
        shutil.rmtree(temp_dir)

def generate_shell_script(commands: list[str], shell_type: str, parameters: Dict[str, Any] = None) -> str:
    """Generates a script with the appropriate shell type and parameter handling."""
    if shell_type not in SUPPORTED_SHELLS:
        raise ValueError(f"Unsupported shell type: {shell_type}")

    shell_info = SUPPORTED_SHELLS[shell_type]
    
    if shell_type == 'python':
        return generate_python_script(commands, parameters or {})
    elif shell_type == 'bash':
        return generate_bash_script(commands, parameters or {})
    elif shell_type == 'batch':
        return generate_batch_script(commands, parameters or {})

def generate_bash_script(commands: list[str], parameters: Dict[str, Any]) -> str:
    script_lines = [
        "#!/bin/bash",
        "",
        "# Handle parameters",
    ]
    
    # Add parameter handling
    for name, config in parameters.items():
        if config.get('required', False):
            script_lines.extend([
                f'if [ -z "${{{name}}}" ]; then',  # Fix variable reference
                f'    read -p "Enter value for {name}: " {name}',
                'fi'
            ])
    
    script_lines.extend(["", "# Execute commands"])
    for cmd in commands:
        if parameters:
            # Use bash variable substitution
            for param in parameters:
                cmd = cmd.replace(f'{{{param}}}', f'"${{{param}}}"')  # Fix variable reference
        script_lines.append(cmd)
    
    return "\n".join(script_lines)

def generate_batch_script(commands: list[str], parameters: Dict[str, Any]) -> str:
    script_lines = [
        "@echo off",
        "",
        "rem Handle parameters",
    ]
    
    # Add parameter handling
    for name, config in parameters.items():
        if config.get('required', False):
            script_lines.extend([
                f'if "%{name}%" == "" (',
                f'    set /p {name}="Enter value for {name}: "',
                ')'
            ])
    
    script_lines.extend(["", "rem Execute commands"])
    for cmd in commands:
        if parameters:
            # Use batch variable substitution
            for param in parameters:
                cmd = cmd.replace(f'{{{param}}}', f'%{param}%')
        script_lines.append(cmd)
    
    return "\n".join(script_lines)  # Fixed string join syntax

def generate_python_script(commands: list[str], parameters: Dict[str, Any]) -> str:
    """Generates a Python script with parameter validation and command execution."""
    script_lines = [
        "#!/usr/bin/env python3",
        "import subprocess",
        "import click",
        "import sys",
        "",
        "@click.command()",
    ]
    
    # Add parameters as click options with prompts
    for name, config in parameters.items():
        param_type = config.get('type', 'string')
        required = config.get('required', False)
        option_str = f'@click.option("--{name}"'
        if required:
            option_str += ', required=True'
            option_str += f', prompt="Enter value for {name}"'  # Add prompt for required params
        if param_type == 'integer':
            option_str += ', type=int'
        script_lines.append(option_str + ')')
    
    # Add argument handler for direct command-line input
    script_lines.extend([
        "@click.argument('args', nargs=-1)",
        "def main(**kwargs):",
        "    # Handle command-line arguments if provided",
        "    args = kwargs.pop('args', [])",
        "    if args:",
        "        for name, config in parameters.items():",
        "            if not kwargs.get(name) and args:",
        "                kwargs[name] = args[0]",
        "                args = args[1:]",
        "",
        "    commands = [",
    ])
    
    # Add commands with parameter substitution
    for cmd in commands:
        script_lines.append(f'        f"""{cmd}""",')
    
    script_lines.extend([
        "    ]",
        "    for cmd in commands:",
        "        try:",
        "            formatted_cmd = cmd.format(**kwargs)",
        "            click.echo(f'Executing: {formatted_cmd}')",
        "            subprocess.run(formatted_cmd, shell=True, check=True)",
        "        except Exception as e:",
        '            click.echo(f"Warning: Command failed: {e}")',
        "",
        'if __name__ == "__main__":',
        "    main()",
    ])
    
    return "\n".join(script_lines)

def create_spell_bundle_from_directory(spell_dir: Path, spell_name: str, description: str, shell_type: str = None) -> Path:
    """Creates a spell bundle (.spell ZIP file) from a directory containing the spell scripts and templates."""
    tome_dir = Path(SANCTUM_PATH) / '.tome'
    tome_dir.mkdir(parents=True, exist_ok=True)

    spell_path = tome_dir / f"{spell_name}.spell"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Copy contents
        shutil.copytree(spell_dir, temp_path, dirs_exist_ok=True)

        # Find main script
        main_script = None
        # First try exact name match
        for ext in ['.py', '.sh']:
            possible_script = temp_path / f"{spell_name}{ext}"
            if possible_script.is_file():
                main_script = f"{spell_name}{ext}"
                break

        # If no exact match, look for alternatives
        if not main_script:
            script_files = list(temp_path.glob("*.py")) + list(temp_path.glob("*.sh"))
            if len(script_files) == 1:
                main_script = script_files[0].name
            elif len(script_files) > 1:
                click.echo("Multiple script files detected:")
                for idx, fname in enumerate(script_files, start=1):
                    click.echo(f"{idx}. {fname.name}")
                choice = click.prompt("Select the main script by number", type=int)
                main_script = script_files[choice - 1].name
            else:
                click.echo(f"No script files found in '{spell_dir}'")
                return None

        # Create metadata
        metadata = {
            'name': spell_name,
            'description': description,
            'created_at': datetime.now(UTC).isoformat(),
            'main_script': main_script,
            'shell_type': shell_type or 'bash'
        }
        
        metadata_path = temp_path / 'spell.json'
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')

        # Create spell bundle
        with zipfile.ZipFile(spell_path, 'w', zipfile.ZIP_DEFLATED) as spell_zip:
            for file_path in temp_path.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(temp_path)
                    spell_zip.write(file_path, arcname)

    return spell_path

def create_spell_from_commands(commands: list[str], spell_name: str, description: str, shell_type: str) -> Path:
    """Creates a spell bundle from a list of commands."""
    temp_dir = Path(tempfile.mkdtemp(prefix='magi_spell_'))
    try:
        # Create script with appropriate shell
        script_content = generate_shell_script(commands, shell_type)
        extension = SUPPORTED_SHELLS[shell_type]['extension']
        
        script_path = temp_dir / f"{spell_name}{extension}"
        script_path.write_text(script_content)
        
        # Create metadata with shell type
        metadata = create_spell_metadata(spell_name, description, shell_type)
        metadata_path = temp_dir / 'spell.json'
        metadata_path.write_text(json.dumps(metadata, indent=2))
        
        return create_spell_bundle_from_directory(temp_dir, spell_name, description, shell_type)
    finally:
        shutil.rmtree(temp_dir)

@click.command()
@click.argument('args', nargs=-1)
def spellcraft(args):
    """'sc' - Weaves a macro spell out of commands or bundles an existing directory."""
    if not args:
        click.echo("Usage:\nCreate from commands: cast sc <num_commands> <spell_name>\n"
                  "Bundle directory: cast sc <directory>\n"
                  "From YAML: cast sc spell.yaml")
        return

    # Check if first argument is a YAML file
    if str(args[0]).endswith('.yaml'):
        try:
            yaml_path = Path(args[0])
            if not yaml_path.is_file():
                click.echo(f"Error: YAML file '{args[0]}' not found")
                return
            
            spell_name = yaml_path.stem
            bundle_path = create_spell_bundle_from_yaml(yaml_path, spell_name)
            if bundle_path:
                click.echo(f"Success: Spell '{spell_name}' created at: {bundle_path}")
            return
        except Exception as e:
            click.echo(f"Error creating spell from YAML: {str(e)}")
            return

    try:
        # Try to interpret first arg as number of commands
        num_commands = int(args[0])
        if len(args) < 2:
            click.echo("Error: Spell name required when creating from commands")
            return
        
        spell_name = args[1]
        description = click.prompt("Enter a description for the spell")
        
        # Collect commands
        commands = []
        for i in range(num_commands):
            cmd = click.prompt(f"Enter command {i + 1}")
            commands.append(cmd)
        
        # Show available shell types and create spell
        click.echo("\nAvailable shell types:")
        for shell_type, info in SUPPORTED_SHELLS.items():
            click.echo(f"  - {shell_type}: {info['description']}")
        
        shell_type = click.prompt(
            "Select shell type",
            type=click.Choice(list(SUPPORTED_SHELLS.keys())),
            default='bash'
        )
        
        bundle_path = create_spell_from_commands(commands, spell_name, description, shell_type)
        if bundle_path:
            click.echo(f"Success: Spell '{spell_name}' created at: {bundle_path}")
        
    except ValueError:
        # Handle directory bundling
        spell_dir = Path(args[0])
        if not spell_dir.is_dir():
            if args[0].endswith('.yaml'):
                click.echo("To use YAML files, use: cast sc --yaml <yaml_file>")
            else:
                click.echo(f"Error: '{spell_dir}' is not a directory")
            return
        
        spell_name = spell_dir.name.removesuffix('.spell')
        description = click.prompt("Enter a description for the spell")
        
        shell_type = click.prompt(
            "Select shell type",
            type=click.Choice(list(SUPPORTED_SHELLS.keys())),
            default='bash'
        )
        
        bundle_path = create_spell_bundle_from_directory(spell_dir, spell_name, description, shell_type)
        if bundle_path:
            click.echo(f"Success: Spell '{spell_name}' created at: {bundle_path}")


alias = 'sc'

# Keep simple command structure
if __name__ == '__main__':
    spellcraft()
