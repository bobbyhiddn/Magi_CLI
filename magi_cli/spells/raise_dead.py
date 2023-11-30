import click
import os
import shutil
import fnmatch
from datetime import datetime

@click.command()
@click.argument('file_paths', nargs=-1, required=False)  # Accepts a variable number of arguments
def raise_dead(file_paths):
    """ 'rd' - Restore a spirit from the graveyard."""
    spirit = file_paths[0] if file_paths else None

    if spirit:
        # Existing code to handle a specific spirit
        source_path = os.path.join(".graveyard", spirit)
        # ...

    else:
        # List spirits and prompt for selection if no specific spirit is provided
        click.echo("The spirits in the graveyard are:")
        for file in os.listdir(".graveyard"):
            click.echo(file)
        spirit = click.prompt("Which spirit would you like to raise?", type=str)
        source_path = os.path.join(".graveyard", spirit)
        if os.path.exists(source_path):
            destination_path = os.path.join(".", "undead_" + spirit)
            shutil.move(source_path, destination_path)
            click.echo(f"The spirit of {spirit} has been restored to this realm, now known as undead_{spirit}.")

alias = "rd"

if __name__ == '__main__':
    raise_dead()