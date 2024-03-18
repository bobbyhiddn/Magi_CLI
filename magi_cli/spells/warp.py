import os
import click
import paramiko
import json
import subprocess
import time
from threading import Lock
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend

# Define the path for the .circle file within the SANCTUM_PATH
SANCTUM_PATH = os.getenv('SANCTUM_PATH', os.path.expanduser('~/.sanctum'))
CIRCLE_PATH = os.path.join(SANCTUM_PATH, '.circle')
KEY_PATH = os.path.join(SANCTUM_PATH, 'keys')
circle_lock = Lock()

# Ensure the SANCTUM_PATH exists
os.makedirs(SANCTUM_PATH, exist_ok=True)
os.makedirs(KEY_PATH, exist_ok=True)

@click.group(invoke_without_command=True)
@click.argument('args', nargs=-1)
@click.pass_context
def warp(ctx, args):
    """ 'wp' - Warp to remote SSH sessions with ease."""
    alias = None if not args else args[0]
    sessions = load_sessions()

    while True:
        if not alias:
            list_sessions(sessions)
            selected_session = click.prompt("Choose a session number or 'E' to edit the circle", default="")
            if selected_session.upper() == 'E':
                result = delete_session(sessions)
                if result == 'WARP':
                    continue
                return
            elif selected_session.isdigit() and int(selected_session) <= len(sessions):
                alias = list(sessions.keys())[int(selected_session) - 1]
            else:
                click.echo("Bypassing the mystical session selection.")
                continue

        if alias in sessions:
            click.echo(f"Warping to {alias}...")
            connect_to_host(sessions[alias])
        else:
            if click.confirm(f"Host '{alias}' not found in your teleportation circle. Would you like to register it and forge a mystical connection?"):
                sessions[alias] = register_host(alias, sessions)
                save_sessions(sessions)
            else:
                click.echo("The arcane energies remain undisturbed. Operation cancelled.")
        ctx.exit()

def generate_rsa_keys(alias):
    private_key_path = os.path.join(KEY_PATH, f'{alias}.pem')
    public_key_path = f"{private_key_path}.pub"

    if not os.path.exists(private_key_path):
        key = rsa.generate_private_key(
            backend=crypto_default_backend(),
            public_exponent=65537,
            key_size=2048
        )
        private_key = key.private_bytes(
            crypto_serialization.Encoding.PEM,
            crypto_serialization.PrivateFormat.PKCS8,
            crypto_serialization.NoEncryption()
        )
        public_key = key.public_key().public_bytes(
            crypto_serialization.Encoding.OpenSSH,
            crypto_serialization.PublicFormat.OpenSSH
        )

        with open(private_key_path, 'wb') as f:
            f.write(private_key)

        with open(public_key_path, 'wb') as f:
            f.write(public_key)

        click.echo(f"A new talisman has been forged in secrecy: {private_key_path}")
    else:
        click.echo(f"The talisman already exists: {private_key_path}")

    return private_key_path

# Function to append public key to authorized_keys on the server
def append_public_key_to_authorized_keys(hostname, username, private_key_path):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.load_system_host_keys()

    try:
        ssh.connect(hostname=hostname, username=username, key_filename=private_key_path)
        click.echo("Connected to host to append public key.")
        
        public_key_path = f"{private_key_path}.pub"
        with open(public_key_path, 'r') as public_key_file:
            public_key = public_key_file.read()
            ssh.exec_command(f'echo "{public_key}" >> ~/.ssh/authorized_keys')
            click.echo("Public key appended to remote authorized_keys.")
    except Exception as e:
        click.echo(f"Error appending public key: {e}")
    finally:
        ssh.close()

# Load existing sessions from CIRCLE_PATH
def load_sessions():
    with circle_lock:
        if os.path.exists(CIRCLE_PATH):
            with open(CIRCLE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

# List all registered sessions
def list_sessions(sessions):
    if not sessions:
        click.echo("Your teleportation circle is empty. Invoke 'warp' with an alias to connect or register.")
        return
    for i, (alias, details) in enumerate(sessions.items(), start=1):
        if details is not None:
            click.echo(f"{i}. {alias}: {details['user']}@{details['host']}")
        else:
            click.echo(f"{i}. {alias}: No details available")

# Delete a session
def delete_session(sessions):
    while True:  # Keep showing the sessions until the user decides to quit
        list_sessions(sessions)
        selected_option = click.prompt("Enter the number of the session you want to delete or 'W' to return to warp selection", default="W")

        if selected_option.upper() == 'W':
            return 'WARP'  # Signal to return to the warp menu

        if selected_option.isdigit() and int(selected_option) <= len(sessions):
            session_alias = list(sessions.keys())[int(selected_option) - 1]
            del sessions[session_alias]
            click.echo(f"The arcane link to '{session_alias}' has been severed.")
            # Save the updated sessions back to the file
            save_sessions(sessions)
        else:
            click.echo("Invalid selection. Please choose a valid session number or 'Q' to quit.")

def register_host(alias, sessions):
    """Register a new SSH session with arcane energies."""
    click.echo(f"By the ancient rite of binding, we shall link your essence to another realm...")
    host = click.prompt("Envision the realm's address (Enter the host IP or hostname)")
    user = click.prompt("Whisper the name of your alter ego in that realm (Enter the username)")
    
    key_choice = click.prompt("Do you possess a talisman to bypass the guardians? (Do you want to set or generate a private key?) [G/P]", default="G", show_default=False)
    
    key = None
    if key_choice.upper() == 'G':
        key = generate_rsa_keys(alias)
        append_public_key_to_authorized_keys(host, user, key)
        click.echo("Attempting to bind the talisman with the distant realm...")
        # Attempt to bind the talisman with the distant realm code goes here
        click.echo(f"The talisman has been bound to {user}@{host}.")
    elif key_choice.upper() == 'P':
        key = click.prompt("Reveal the talisman's hiding place (Enter the private key location)")
    else:
        click.echo("The arcane forces are puzzled by your choice. No talisman will be set.")

    # Ensure the .circle file exists and update it with the new host information
    sessions[alias] = {"user": user, "host": host, "key": key}
    save_sessions(sessions)
    
    click.echo(f"The winds of magic swirl and solidify; a new passage to '{alias}' has been established.")

def save_sessions(sessions):
    with circle_lock:
        os.makedirs(os.path.dirname(CIRCLE_PATH), exist_ok=True)
        with open(CIRCLE_PATH, 'w') as f:
            json.dump(sessions, f, indent=2)
            click.echo(f"Host '{alias}' registered successfully.")

        # Debugging: Verify the contents right after writing and sleeping
        with open(CIRCLE_PATH, 'r', encoding='utf-8') as f:
            file_contents = f.read()
        print(f"File contents immediately after saving and sleeping: {file_contents}")  # Debug line

def connect_to_host(session):
    ssh_command = ['ssh']
    if session.get('key'):
        ssh_command += ['-i', session['key']]
    ssh_command.append(f"{session['user']}@{session['host']}")
    subprocess.run(ssh_command)

@warp.command()
@click.argument('alias')
def connect(alias):
    sessions = load_sessions()
    if alias not in sessions:
        click.echo("This realm is unknown to the arcane forces.")
        return
    session = sessions[alias]
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        if 'key' in session:
            key_path = os.path.expanduser(session['key'])
            key = paramiko.RSAKey.from_private_key_file(key_path)
            ssh.connect(session['host'], username=session['user'], pkey=key)
        else:
            ssh.connect(session['host'], username=session['user'])
        click.echo(f"Connected to {alias}.")
        # This part is for demonstration. You might want to implement a full shell or another interaction.
        stdin, stdout, stderr = ssh.exec_command('whoami')
        click.echo(stdout.read().decode())
    finally:
        ssh.close()

alias = "wp"

if __name__ == '__main__':
    warp()
