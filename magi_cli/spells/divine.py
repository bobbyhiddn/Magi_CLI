import click
import os
import fnmatch
from datetime import datetime

@click.command()
@click.argument('args', nargs=-1, required=False)  # Use args to accept variable number of arguments
def divine(args):
    """ 'dv' - List the directory contents with detailed information, or find a file anywhere below the root directory, searching through child directories, and echo its path."""
    
    search_term = args[0] if args else None

    if search_term:
        click.echo(f"You cast your senses into the ether, seeking knowledge of the realm...\n")
        for root, dirs, files in os.walk('.'):
            for file in files:
                if fnmatch.fnmatch(file, f'*{search_term}*'):
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    file_permissions = oct(os.stat(file_path).st_mode)[-3:]
                    file_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                    click.echo(f"{file_path}\tSize: {file_size} bytes\tPermissions: {file_permissions}\tLast Modified: {file_modified}")
    else:
        click.echo(f"You cast your senses into the ether, seeking knowledge of the realm...\n")
        for file in os.listdir("."):
            file_path = os.path.join(".", file)
            file_size = os.path.getsize(file_path)
            file_permissions = oct(os.stat(file_path).st_mode)[-3:]
            file_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
            click.echo(f"{file}\tSize: {file_size} bytes\tPermissions: {file_permissions}\tLast Modified: {file_modified}")

alias = "dv"

def main():
    divine()

if __name__ == '__main__':
    main()