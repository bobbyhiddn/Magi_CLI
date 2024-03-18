import click
import os
import shutil

@click.command()
@click.argument('args', nargs=-1, required=True)  # Accepts multiple file paths
def banish(args):
    ''' 'bn' - Banish a target to the /tmp directory in a .exile folder. If no /tmp directory exists, place it in a C:\\temp\\.exile directory.'''
    
    if not args:
        click.echo("Error: No file path provided.")
        return

    # Handle the first file path from the list
    file_path = args[0]

    # Check if /tmp exists (Unix systems) or use C:\temp (Windows)
    if os.path.exists("/tmp"):
        exile_dir = "/tmp/.exile"
    else:
        exile_dir = "C:\\temp\\.exile"

    if not os.path.exists(exile_dir):
        os.makedirs(exile_dir)

    shutil.move(file_path, os.path.join(exile_dir, os.path.basename(file_path)))
    click.echo(f"{file_path} has been banished to the {exile_dir} directory in a .exile folder.")

alias = "bn"

def main():
    banish()

if __name__ == '__main__':
    main()
