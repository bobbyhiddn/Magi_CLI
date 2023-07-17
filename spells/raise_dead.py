import click
import os
import shutil
import fnmatch
from datetime import datetime

@click.command()
@click.argument('spirit', required=False)
def raise_dead(spirit=None):
    """Restore a spirit from the graveyard."""
    if spirit:
        source_path = os.path.join(".graveyard", spirit)
        if os.path.exists(source_path):
            destination_path = os.path.join(".", "undead_" + spirit)
            shutil.move(source_path, destination_path)
            click.echo(f"The spirit of {spirit} has been restored to this realm, now known as undead_{spirit}.")
        else:
            click.echo("That spirit is not in this graveyard...")
    else:
        click.echo("The spirits in the graveyard are:")
        for file in os.listdir(".graveyard"):
            click.echo(file)
        click.echo("Which spirit would you like to raise?")
        spirit = click.prompt("Spirit name", type=str)
        source_path = os.path.join(".graveyard", spirit)
        if os.path.exists(source_path):
            destination_path = os.path.join(".", "undead_" + spirit)
            shutil.move(source_path, destination_path)
            click.echo(f"The spirit of {spirit} has been restored to this realm, now known as undead_{spirit}.")

