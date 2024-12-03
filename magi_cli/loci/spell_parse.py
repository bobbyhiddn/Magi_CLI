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
from typing import Tuple, Dict, Any, Optional, List
from magi_cli.spells import SANCTUM_PATH
from magi_cli.loci.sigildry import Sigildry

class SpellParser:
    """Parser for spell bundles with enhanced validation."""
    
    # Required metadata fields
    REQUIRED_FIELDS = ['name', 'version', 'description', 'type', 'entry_point']
    ALLOWED_TYPES = ['bundled', 'macro', 'script']  # Updated to include 'script'
    ALLOWED_SHELLS = ['python', 'bash', 'shell']
    ALLOWED_EXTENSIONS = ['.py', '.sh', '.spell', '.fiat']  # Added extensions list
    
    @staticmethod
    def parse_bundle(spell_path: str) -> Tuple[Path, Dict]:
        """
        Parse a spell bundle into a temporary directory and return the path and metadata.
        """
        # Create a temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix='magi_spell_'))

        # Extract the spell bundle
        with zipfile.ZipFile(spell_path, 'r') as zip_ref:
            # Get list of files
            files = zip_ref.namelist()
            
            # Extract files, removing any top-level directory
            for file in files:
                parts = Path(file).parts
                
                # Skip directories, they'll be created when extracting files
                if file.endswith('/'):
                    continue
                
                # Remove top-level directory if present
                if parts[0] == 'ascii_art':
                    target_path = temp_dir / Path(*parts[1:])
                else:
                    target_path = temp_dir / file
                
                # Ensure parent directory exists
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Extract file
                with zip_ref.open(file) as source, open(target_path, 'wb') as target:
                    shutil.copyfileobj(source, target)

        # Find and parse metadata from spell.yaml first (primary source)
        yaml_path = temp_dir / 'spell' / 'spell.yaml'
        metadata = {}
        
        if yaml_path.exists():
            with open(yaml_path) as f:
                import yaml
                metadata = yaml.safe_load(f)
                
            # Update spell.json to match spell.yaml
            json_path = temp_dir / 'spell.json'
            if json_path.exists():
                with open(json_path, 'w') as f:
                    json.dump(metadata, f, indent=2)

        # Verify spell sigil using Sigildry
        sigil_verification = Sigildry.verify_sigil(spell_path)
        
        # Add sigil verification details to metadata
        metadata['sigil_verification'] = {
            'status': sigil_verification.get('verification_status', 'Unknown'),
            'details': sigil_verification.get('details', 'No details'),
            'verified': sigil_verification.get('verified', False),
            'current_hash': sigil_verification.get('current_hash'),
            'stored_hash': sigil_verification.get('stored_hash')
        }
        
        # Validate and set default metadata
        SpellParser._validate_metadata(metadata)
        
        # Check dependencies
        if not SpellParser.check_dependencies(metadata.get('dependencies', {})):
            raise ValueError("Cannot proceed: missing required dependencies")
        
        # Ensure requires/dependencies are consistent
        if 'requires' not in metadata and 'dependencies' in metadata:
            metadata['requires'] = metadata['dependencies'].get('python', [])
        
        return temp_dir, metadata
                
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
            
        # Validate dependencies format if present
        if 'dependencies' in metadata:
            if not isinstance(metadata['dependencies'], dict):
                raise ValueError("Dependencies must be a dictionary")
            if 'python' in metadata['dependencies'] and not isinstance(metadata['dependencies']['python'], list):
                raise ValueError("Python dependencies must be a list")

    @staticmethod
    def _convert_yaml_to_metadata(config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert legacy spell.yaml format to standardized metadata."""
        # Handle requires field - ensure it's a list
        requires = []
        if 'requires' in config:
            if isinstance(config['requires'], list):
                requires = config['requires']
            elif isinstance(config['requires'], str):
                requires = [config['requires']]
                
        # Create dependencies dict with python key if we have requires
        dependencies = {'python': requires} if requires else {}
        
        metadata = {
            'name': config.get('name'),
            'version': config.get('version', '1.0.0'),
            'description': config.get('description', ''),
            'type': config.get('type', 'bundled'),
            'shell_type': config.get('shell_type', 'python'),
            'entry_point': config.get('entry_point'),
            'parameters': config.get('parameters', {}),
            'dependencies': dependencies,
            'created_at': '',  # Set during bundling
            'sigil_hash': None  # Calculated during bundling
        }
        return metadata

    @staticmethod
    def check_dependencies(
        dependencies: Dict[str, List[str]], 
        verbose: bool = False
    ) -> bool:
        """
        Check if required dependencies are installed.
        
        Args:
            dependencies (Dict[str, List[str]]): Dictionary of dependencies
            verbose (bool, optional): Show detailed dependency information
        
        Returns:
            bool: True if all dependencies are satisfied, False otherwise
        """
        try:
            import importlib.util
            
            # If no dependencies, return True
            if not dependencies or 'python' not in dependencies:
                return True
            
            python_deps = dependencies['python']
            
            # If no Python dependencies, return True
            if not python_deps:
                return True
            
            # Track missing dependencies
            missing_deps = []
            
            # Check each dependency
            for dep in python_deps:
                # Extract package name (handle various version specifiers)
                pkg_name = dep.split('>=')[0].split('~=')[0].split('==')[0].strip()
                
                try:
                    spec = importlib.util.find_spec(pkg_name)
                    if spec is None:
                        missing_deps.append(dep)
                except ImportError:
                    missing_deps.append(dep)
            
            # Verbose output for dependencies
            if verbose and missing_deps:
                click.echo(click.style("\nDependency Check:", fg='bright_cyan', bold=True))
                click.echo(click.style("  Missing Packages:", fg='bright_red'))
                for dep in missing_deps:
                    click.echo(f"    - {dep}")
            
            # If missing dependencies, prompt to install
            if missing_deps:
                if verbose:
                    install_prompt = click.style("  Would you like to install these dependencies?", fg='bright_white')
                    if click.confirm(install_prompt, default=True):
                        try:
                            import subprocess
                            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_deps)
                            click.echo(click.style("  Dependencies installed successfully!", fg='bright_green'))
                            return True
                        except subprocess.CalledProcessError:
                            click.echo(click.style("  Failed to install dependencies", fg='bright_red'))
                            return False
                return False
            
            return True
        
        except Exception as e:
            if verbose:
                click.echo(click.style(f"Dependency check error: {e}", fg='bright_red'))
            return False

    @classmethod
    def find_spell_file(cls, spell_name: str) -> Path:
        """
        Find the spell file in the .tome directory.
        
        Args:
            spell_name (str): Name of the spell to find
        
        Returns:
            Path: Full path to the spell file
        """
        # Ensure spell name has .spell extension
        if not spell_name.endswith('.spell'):
            spell_name += '.spell'
        
        # Potential paths to search
        potential_paths = [
            Path(SANCTUM_PATH) / '.tome' / spell_name,  # Exact match in .tome
            Path(SANCTUM_PATH) / '.tome' / f"{spell_name.split('.')[0]}.spell",  # Alternate case
            Path(os.path.expanduser('~')) / '.sanctum' / '.tome' / spell_name,  # User home directory
        ]
        
        # Search through potential paths
        for path in potential_paths:
            if path.exists():
                return path
        
        # If no spell found, raise an error
        raise FileNotFoundError(f"Could not find spell '{spell_name}' in .tome directory")

    @classmethod
    def execute_spell_file(
        cls, 
        spell_name: str, 
        *args: str, 
        verbose: int = 0
    ) -> bool:
        """
        Execute a spell from the .tome directory.
        
        Args:
            spell_name (str): Name of the spell to execute
            *args (str): Additional arguments to pass to the spell
            verbose (int, optional): Verbosity level. 0 = silent, 1 = basic info, 2 = detailed info
        
        Returns:
            bool: True if spell execution was successful, False otherwise
        """
        try:
            # Resolve spell path in .tome directory
            tome_path = Path(SANCTUM_PATH) / '.tome'
            spell_path = tome_path / f"{spell_name}.spell"
            
            if not spell_path.exists():
                click.echo(f"Error: Spell '{spell_name}' not found in tome.")
                return False
            
            # Verify spell sigil
            from magi_cli.loci.sigildry import Sigildry
            sigil_verification = Sigildry.verify_sigil(spell_path)
            
            # Parse the spell bundle
            try:
                if verbose >= 2:
                    click.echo("\nExtracting spell bundle:")
                    click.echo(f"  From: {spell_path}")
                
                temp_dir, metadata = SpellParser.parse_bundle(spell_path)
                
                if verbose >= 2:
                    click.echo(f"  To: {temp_dir}")
                    click.echo("\nListing extracted files:")
                    for root, dirs, files in os.walk(temp_dir):
                        rel_path = os.path.relpath(root, temp_dir)
                        if rel_path == '.':
                            for f in files:
                                click.echo(f"  - {f}")
                        else:
                            for f in files:
                                click.echo(f"  - {rel_path}/{f}")
            except Exception as e:
                click.echo(f"Error parsing spell bundle: {e}")
                return False
            
            # Level 1 verbosity (basic info)
            if verbose >= 1:
                click.echo(f"Executing Spell: {metadata.get('name', spell_name)}")
                click.echo(f"Description: {metadata.get('description', 'No description')}")
                click.echo(f"Type: {metadata.get('type', 'Unknown')}")
                click.echo(f"Shell Type: {metadata.get('shell_type', 'Unknown')}")
            
            # Locate the entry point script
            entry_point_name = metadata.get('entry_point')
            if not entry_point_name:
                click.echo("Error: No entry point found in spell metadata.")
                return False
            
            # Find the actual entry point file
            entry_point_candidates = [
                temp_dir / 'spell' / entry_point_name,  # Primary location in spell/
                temp_dir / entry_point_name,  # Fallback to root
                temp_dir / 'spell' / 'spell' / entry_point_name  # Legacy location
            ]
            
            if verbose >= 2:
                click.echo("\nSearching for entry point:")
                for path in entry_point_candidates:
                    click.echo(f"  Checking: {path}")
                    if path.exists():
                        click.echo(f"  Found at: {path}")
                        break
            
            entry_point = next((path for path in entry_point_candidates if path.exists()), None)
            
            if not entry_point:
                click.echo(f"Error: Entry point {entry_point_name} not found.")
                return False
            
            # Make the script executable if it's a shell script
            if entry_point.suffix == '.sh':
                entry_point.chmod(0o755)
            
            # Determine execution method based on file type
            shell_type = metadata.get('shell_type', 'python')
            
            try:
                if shell_type == 'python':
                    # Use subprocess to run Python script
                    result = subprocess.run(
                        [sys.executable, str(entry_point), *args], 
                        capture_output=True, 
                        text=True
                    )
                    
                    # Handle Python script output
                    if result.stdout:
                        click.echo(result.stdout)
                    if result.stderr:
                        click.echo(result.stderr, err=True)
                    
                    # Check return code
                    if result.returncode != 0:
                        click.echo(f"Python spell execution failed with code {result.returncode}")
                        return False
                
                elif shell_type in ['bash', 'shell']:
                    # Use subprocess to run shell script
                    result = subprocess.run(
                        ['bash', str(entry_point), *args], 
                        capture_output=True, 
                        text=True
                    )
                    
                    # Handle shell script output
                    if result.stdout:
                        click.echo(result.stdout)
                    if result.stderr:
                        click.echo(result.stderr, err=True)
                    
                    # Check return code
                    if result.returncode != 0:
                        click.echo(f"Shell spell execution failed with code {result.returncode}")
                        return False
                
                else:
                    click.echo(f"Unsupported shell type: {shell_type}")
                    return False
            
            except Exception as e:
                click.echo(f"Execution error: {e}")
                return False
            
            # Level 2 verbosity (detailed metadata)
            if verbose >= 2:
                click.echo("\nDetailed Spell Metadata:")
                for key, value in metadata.items():
                    # Skip empty or None values
                    if value is None or (isinstance(value, (str, list, dict)) and len(value) == 0):
                        continue
                    
                    # Skip code display and sigil verification (will show separately)
                    if key in ['code', 'sigil_verification']:
                        continue
                    
                    # Special handling for nested dictionaries
                    if isinstance(value, dict):
                        click.echo(f"  {click.style(key.upper(), fg='bright_cyan', bold=True)}:")
                        for sub_key, sub_value in value.items():
                            # Skip empty or None sub-values
                            if sub_value is not None and not (isinstance(sub_value, (str, list, dict)) and len(sub_value) == 0):
                                click.echo(f"    {click.style(sub_key + ':', fg='bright_white')} {sub_value}")
                    else:
                        click.echo(f"  {click.style(key.upper() + ':', fg='bright_cyan')} {value}")
                
                # Add sigil verification details
                click.echo("\n  SIGIL VERIFICATION:")
                verification_details = sigil_verification
                for sub_key, sub_value in verification_details.items():
                    if sub_key != 'metadata':  # Skip nested metadata
                        click.echo(f"    {click.style(sub_key.upper() + ':', fg='bright_white')} {sub_value}")
            
            return True
        
        except Exception as e:
            click.echo(f"Unexpected error executing spell: {e}")
            return False
        finally:
            # Clean up temporary directory
            import shutil
            if 'temp_dir' in locals() and Path(temp_dir).exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

    @staticmethod
    def execute_python_file(script_path: str, args=None, verbose: bool = False) -> bool:
        """
        Execute a Python script with optional arguments.
        
        Args:
            script_path (str): Path to the Python script
            args (list, optional): Arguments to pass to the script
            verbose (bool, optional): Show detailed execution information
        
        Returns:
            bool: True if execution was successful, False otherwise
        """
        try:
            # Prepare the command
            cmd = [sys.executable, script_path] + (args or [])
            
            if verbose:
                # Detailed command execution logging
                click.echo(click.style("Python Script Execution:", fg='bright_cyan', bold=True))
                click.echo(f"  {click.style('Script Path:', fg='bright_white')} {script_path}")
                click.echo(f"  {click.style('Command:', fg='bright_white')} {' '.join(cmd)}")
            
            # Run the script
            result = subprocess.run(cmd, capture_output=verbose, text=verbose)
            
            # If verbose, show output
            if verbose and result.stdout:
                click.echo(click.style("\nScript Output:", fg='bright_cyan', bold=True))
                click.echo(result.stdout)
            
            # Check for errors
            if result.returncode != 0 and verbose:
                click.echo(click.style("\nScript Execution Error:", fg='bright_red', bold=True))
                click.echo(result.stderr)
                return False
            
            return True
        
        except subprocess.CalledProcessError:
            if verbose:
                click.echo(click.style("Script Execution Failed", fg='bright_red', bold=True))
            return False

    @staticmethod
    def execute_bash_file(script_path: str, verbose: bool = False) -> bool:
        """
        Execute a bash script with platform-specific handling.
        
        Args:
            script_path (str): Path to the bash script
            verbose (bool, optional): Show detailed execution information
        
        Returns:
            bool: True if execution was successful, False otherwise
        """
        try:
            # Determine appropriate shell
            if sys.platform == 'win32':
                # Use Git Bash or WSL
                if shutil.which('bash'):
                    cmd = ['bash', script_path]
                elif shutil.which('wsl'):
                    cmd = ['wsl', 'bash', script_path]
                else:
                    if verbose:
                        click.echo(click.style("No bash shell found", fg='bright_red', bold=True))
                    return False
            else:
                # Unix-like systems
                cmd = ['bash', script_path]
            
            if verbose:
                # Detailed command execution logging
                click.echo(click.style("Bash Script Execution:", fg='bright_cyan', bold=True))
                click.echo(f"  {click.style('Script Path:', fg='bright_white')} {script_path}")
                click.echo(f"  {click.style('Command:', fg='bright_white')} {' '.join(cmd)}")
            
            # Run the script
            result = subprocess.run(cmd, capture_output=verbose, text=verbose)
            
            # If verbose, show output
            if verbose and result.stdout:
                click.echo(click.style("\nScript Output:", fg='bright_cyan', bold=True))
                click.echo(result.stdout)
            
            # Check for errors
            if result.returncode != 0 and verbose:
                click.echo(click.style("\nScript Execution Error:", fg='bright_red', bold=True))
                click.echo(result.stderr)
                return False
            
            return True
        
        except subprocess.CalledProcessError as e:
            if verbose:
                click.echo(click.style("Failed to execute script", fg='bright_red', bold=True))
                click.echo(str(e))
            return False
        except FileNotFoundError:
            if verbose:
                click.echo(click.style("Bash shell not found", fg='bright_red', bold=True))
            return False