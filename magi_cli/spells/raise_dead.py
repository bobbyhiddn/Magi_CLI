import click
import os
import shutil
from magi_cli.spells import SANCTUM_PATH  # Import SANCTUM_PATH

@click.command()
@click.argument('args', nargs=-1, required=False)  # Accepts a variable number of arguments
def raise_dead(args):
    """ 'rd' - Restore a spirit from the graveyard."""
    graveyard_path = os.path.join(SANCTUM_PATH, '.graveyard')  # Use SANCTUM_PATH for .graveyard directory

    spirit = args[0] if args else None

    if spirit:
        # Handle a specific spirit
        source_path = os.path.join(graveyard_path, spirit)
        if os.path.exists(source_path):
            destination_path = os.path.join(".", "undead_" + spirit)
            shutil.move(source_path, destination_path)
            click.echo(f"The spirit of {spirit} has been restored to this realm, now known as undead_{spirit}.")
        else:
            click.echo(f"No spirit named {spirit} found in the graveyard.")

    else:
        # List spirits and prompt for selection if no specific spirit is provided
        if os.path.exists(graveyard_path) and os.listdir(graveyard_path):
            click.echo("The spirits in the graveyard are:")
            for file in os.listdir(graveyard_path):
                click.echo(file)
            spirit = click.prompt("Which spirit would you like to raise?", type=str)
            source_path = os.path.join(graveyard_path, spirit)
            if os.path.exists(source_path):
                destination_path = os.path.join(".", "undead_" + spirit)
                shutil.move(source_path, destination_path)
                click.echo(f"The spirit of {spirit} has been restored to this realm, now known as undead_{spirit}.")
            else:
                click.echo(f"No spirit named {spirit} found in the graveyard.")
        else:
            click.echo("The graveyard is empty. There are no spirits to raise.")

alias = "rd"

def main():
    raise_dead()

if __name__ == '__main__':
    main()