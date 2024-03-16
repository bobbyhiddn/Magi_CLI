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
    sessions = load_sessions()

    if not args:
        click.echo("Available SSH sessions:")
        list_sessions(sessions)
        ctx.exit()

    alias = args[0]

    if alias in sessions:
        connect_to_host(sessions[alias])
    else:
        if click.confirm(f"Host '{alias}' not found. Would you like to register it?"):
            # Pass 'sessions' as an argument to 'register_host'
            register_host(alias, sessions)
            save_sessions(sessions)
            click.echo(f"Host '{alias}' registered successfully.")
        else:
            click.echo("Operation cancelled.")

def load_sessions():
    if os.path.exists(CIRCLE_PATH):
        with open(CIRCLE_PATH, 'r') as f:
            return json.load(f)
    return {}

def save_sessions(sessions):
    os.makedirs(os.path.dirname(CIRCLE_PATH), exist_ok=True)
    with open(CIRCLE_PATH, 'w') as f:
        json.dump(sessions, f, indent=4)

def list_sessions(sessions):
    for alias, details in sessions.items():
        click.echo(f"{alias}: {details['user']}@{details['host']}")

def connect_to_host(session):
    ssh_command = ['ssh']
    if session.get('key'):
        ssh_command += ['-i', session['key']]
    if session.get('password'):
        ssh_command += ['-o', 'PasswordAuthentication=yes']
    ssh_command.append(f"{session['user']}@{session['host']}")
    subprocess.run(ssh_command)

def register_host(alias, sessions):
    """Register a new SSH session."""
    click.echo("Starting the registration wizard...")
    host = click.prompt("Enter the host IP or hostname")
    user = click.prompt("Enter the username")
    
    password = None
    if click.confirm("Do you want to set a password?"):
        try:
            # Try to use getpass first
            password = getpass("Enter the password: ")
        except (EOFError, KeyboardInterrupt):
            # Use click.prompt as a fallback
            password = click.prompt("Enter the password", hide_input=True, confirmation_prompt=True)
    
    key = None
    if click.confirm("Do you want to set a private key?"):
        key = click.prompt("Enter the private key location")
    
    # Update and save the .circle file with the new host information
    sessions[alias] = {"user": user, "host": host, "password": password, "key": key}
    if not os.path.exists(CIRCLE_PATH):
        os.makedirs(os.path.dirname(CIRCLE_PATH), exist_ok=True)
    
    with open(CIRCLE_PATH, 'w') as f:
        json.dump(sessions, f, indent=2)
    click.echo(f"Host '{alias}' registered successfully.")


alias = "wp"

if __name__ == '__main__':
    warp()
