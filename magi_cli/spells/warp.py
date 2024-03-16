import click
import os
import subprocess
import json
from getpass import getpass
from magi_cli.spells import SANCTUM_PATH

# Define the path for the .circle file within the SANCTUM_PATH
CIRCLE_PATH = os.path.join(SANCTUM_PATH, '.circle')

@click.group(invoke_without_command=True)
@click.argument('args', nargs=-1)
@click.pass_context
def warp(ctx, args):
    """ 'wp' - Warp to remote SSH sessions with ease."""
    # Load the saved SSH sessions from the .circle file
    if os.path.exists(CIRCLE_PATH):
        with open(CIRCLE_PATH, 'r') as f:
            sessions = json.load(f)
    else:
        sessions = {}

    if not args:
        # If no args are provided, show the help message.
        print(ctx.get_help())
        return

    alias = args[0]

    if alias in sessions:
        # If an alias is provided and found, connect to that SSH session
        connect_to_host(sessions[alias])
    else:
        # If the alias is not found, go through registration wizard
        if click.confirm(f"Host '{alias}' not found. Would you like to register it?"):
            register_host(alias, sessions)
        else:
            click.echo("Operation cancelled.")

def connect_to_host(session):
    """Connect to a saved SSH session."""
    ssh_command = ['ssh']
    if 'key' in session:
        ssh_command.extend(['-i', session['key']])
    if 'password' in session:
        ssh_command.extend(['-o', 'PasswordAuthentication=yes'])
    ssh_command.append(f"{session['user']}@{session['host']}")
    subprocess.run(ssh_command)

def register_host(alias, sessions):
    """Register a new SSH session."""
    host = click.prompt("Enter the host IP or hostname")
    user = click.prompt("Enter the username")
    password = getpass("Enter the password") if click.confirm("Do you want to set a password?") else None
    key = click.prompt("Enter the private key location") if click.confirm("Do you want to set a private key?") else None

    # Add the new session to the .circle file
    sessions[alias] = {
        "user": user,
        "host": host,
        "password": password,
        "key": key
    }

    # Ensure the .circle file exists
    if not os.path.exists(CIRCLE_PATH):
        os.makedirs(os.path.dirname(CIRCLE_PATH), exist_ok=True)

    with open(CIRCLE_PATH, 'w') as f:
        json.dump(sessions, f, indent=2)
    click.echo(f"Host '{alias}' registered successfully.")

if __name__ == '__main__':
    warp()
