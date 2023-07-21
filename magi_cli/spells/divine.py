import click
import os
import shutil
import fnmatch
from datetime import datetime

@click.command()
@click.argument('search_term', required=False)
def divine(search_term):
    """List the directory contents with detailed information, or find a file anywhere below the root directory, searching through child directories, and echo its path."""
    if search_term:
        click.echo(f"You cast your senses into the ether, seeking knowledge of the realm...\n")
        for root, dirs, files in os.walk('.'):  # Start search from the root directory
            for file in files:
                if fnmatch.fnmatch(file, f'*{search_term}*'):  # If the file name contains the search term
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    file_permissions = oct(os.stat(file_path).st_mode)[-3:]
                    file_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                    click.echo(f"{file_path}\tSize: {file_size} bytes\tPermissions: {file_permissions}\tLast Modified: {file_modified}")
    else:
        # If no search term was supplied, the function behaves as before
        click.echo(f"You cast your senses into the ether, seeking knowledge of the realm...\n")
        for file in os.listdir("."):
            file_path = os.path.join(".", file)
            file_size = os.path.getsize(file_path)
            file_permissions = oct(os.stat(file_path).st_mode)[-3:]
            file_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
            click.echo(f"{file}\tSize: {file_size} bytes\tPermissions: {file_permissions}\tLast Modified: {file_modified}")
