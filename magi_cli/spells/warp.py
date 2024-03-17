import click
import os
import subprocess
import json
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
        selected_session = click.prompt("Select a session number (or press Enter to bypass)", default="")
        if selected_session.isdigit() and int(selected_session) <= len(sessions):
            alias = list(sessions.keys())[int(selected_session) - 1]
            connect_to_host(sessions[alias])
        else:
            click.echo("Bypassing session selection.")
        ctx.exit()

    alias = args[0]

    if alias in sessions:
        connect_to_host(sessions[alias])
    else:
        if click.confirm(f"Host '{alias}' not found. Would you like to register it?"):
            sessions[alias] = register_host(alias)
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
    ssh_command.append(f"{session['user']}@{session['host']}")
    subprocess.run(ssh_command)

def register_host(alias):
    """Register a new SSH session."""
    click.echo("Starting the registration wizard...")
    host = click.prompt("Enter the host IP or hostname")
    user = click.prompt("Enter the username")
    
    key = None
    if click.confirm("Do you want to set a private key?"):
        key = click.prompt("Enter the private key location")
    
    # Update and save the .circle file with the new host information
    return {"user": user, "host": host, "key": key}

alias = "wp"

if __name__ == '__main__':
    warp()
