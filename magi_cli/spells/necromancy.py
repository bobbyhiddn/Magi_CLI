import click
import os

@click.command()
def necromancy():
    """ 'nc' - Start a session that keeps a memory of deleted files."""
    path = ".graveyard"
    try:
        os.mkdir(path)
    except FileExistsError:
        click.echo("The dark energies swirl around you... A graveyard already lies here.")
    else:
        click.echo("You weave the spell and a graveyard appears, ready to accept the spirits of the deceased files.")

alias = "nc"

if __name__ == '__main__':
    necromancy()