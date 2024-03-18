import click
import os
from magi_cli.spells import SANCTUM_PATH 

@click.command()
@click.argument('args', nargs=-1, required=False)  # Accepts any number of arguments but doesn't use them
def necromancy(args):
    """ 'nc' - Start a session that keeps a memory of deleted files."""
    graveyard_path = os.path.join(SANCTUM_PATH, '.graveyard')
    try:
        os.mkdir(graveyard_path)
    except FileExistsError:
        click.echo("The dark energies swirl around you... A graveyard already lies here.")
    else:
        click.echo("You weave the spell and a graveyard appears, ready to accept the spirits of the deceased files.")

alias = "nc"

def main():
    necromancy()

if __name__ == '__main__':
    main()