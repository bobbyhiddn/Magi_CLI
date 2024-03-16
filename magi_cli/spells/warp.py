import click
import os
import subprocess
import json
from getpass import getpass
from magi_cli.spells import SANCTUM_PATH

# Define the path for the .circle file within the SANCTUM_PATH
CIRCLE_PATH = os.path.join(SANCTUM_PATH, '.circle')

@click.group()
def warp():
    """Warp to SSH sessions with ease."""
    pass

@warp.command()
@click.argument('alias', required=False)
def connect(alias):
    """Connect to a saved SSH session."""
    # Ensure the .circle file exists
    if not os.path.exists(CIRCLE_PATH):
        os.makedirs(os.path.dirname(CIRCLE_PATH), exist_ok=True)
        with open(CIRCLE_PATH, 'w') as f:
            json.dump({}, f)

    # Load the saved SSH sessions from the .circle file
    with open(CIRCLE_PATH, 'r') as f:
        sessions = json.load(f)

    if alias:
        # If an alias is provided, warp to that SSH session
        if alias in sessions:
            session = sessions[alias]
            ssh_command = ['ssh']
            if 'key' in session:
                ssh_command.extend(['-i', session['key']])
            if 'password' in session:
                ssh_command.extend(['-o', f'PasswordAuthentication=yes'])
            ssh_command.append(f"{session['user']}@{session['host']}")
            subprocess.run(ssh_command)
        else:
            click.echo(f"No saved session for alias '{alias}'")
            if click.confirm("Would you like to register this new host?"):
                register_host(alias)
    else:
        # If no alias is provided, list all saved SSH sessions
        click.echo("Available SSH sessions:")
        for alias, details in sessions.items():
            click.echo(f"- {alias}: {details['user']}@{details['host']}")

@warp.command()
@click.argument('alias', required=False)
def register(alias):
    """Register a new SSH session."""
    if not alias:
        alias = click.prompt("Enter a nickname for the new host")
    register_host(alias)

def register_host(alias):
    """Helper function to register a new host."""
    host = click.prompt("Enter the host IP or hostname")
    user = click.prompt("Enter the username")
    password = None
    if click.confirm("Do you want to set a password?"):
        password = getpass("Enter the password")
    key = None
    if click.confirm("Do you want to set a private key?"):
        key = click.prompt("Enter the private key location")

    # Load or create the .circle file
    if not os.path.exists(CIRCLE_PATH):
        os.makedirs(os.path.dirname(CIRCLE_PATH), exist_ok=True)
        sessions = {}
    else:
        with open(CIRCLE_PATH, 'r') as f:
            sessions = json.load(f)

    # Add the new session to the .circle file
    sessions[alias] = {
        "user": user,
        "host": host,
        "password": password,
        "key": key
    }

    with open(CIRCLE_PATH, 'w') as f:
        json.dump(sessions, f, indent=2)
    click.echo(f"Host '{alias}' registered successfully.")

warp.add_command(connect)
warp.add_command(register)

# Set the alias for the warp spell
alias = "wp"

# Add the warp spell to the incantations
if __name__ == '__main__':
    warp()