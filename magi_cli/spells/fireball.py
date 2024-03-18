import click
import os
import shutil
from magi_cli.spells import SANCTUM_PATH 

@click.command()
@click.argument('args', nargs=-1, required=True)  # Accept multiple file paths
def fireball(args):
    """ 'fb' - Deletes a directory or file."""
    graveyard_path = os.path.join(SANCTUM_PATH, '.graveyard')

    # Check if the graveyard exists
    if not os.path.exists(graveyard_path):
        click.echo("There are no graveyards available. Unable to cast fireball.")
        return  # Break out of the function

    for file_path in args:  # Iterate over each file path provided
        if os.path.exists(file_path):
            click.echo(f"Your hands tremble as you draw upon the arcane energies...\n")

            # Check whether the path is a file or a directory
            if os.path.isfile(file_path):
                confirmation_prompt = "Are you sure you want to continue? A target sent to the graveyard is as dead as can be."
            elif os.path.isdir(file_path):
                confirmation_prompt = "You are about to incinerate a directory and everything within it, sending it to the graveyard. Are you sure you want to continue?"
            else:
                confirmation_prompt = "Are you sure you want to continue? A target sent to the graveyard is as dead as can be."
            
            if click.confirm(confirmation_prompt, abort=True):
                click.echo("You cast the spell and a fireball erupts from your hands, engulfing the target in flames...")
                click.echo("When the smoke clears, nothing remains but cinder and ash.")
                destination_path = os.path.join(graveyard_path, os.path.basename(file_path))
                shutil.move(file_path, destination_path)

                # Clean up the graveyard if it has more than 13 files
                files_in_graveyard = os.listdir(graveyard_path)
                if len(files_in_graveyard) > 13:
                    files_in_graveyard.sort(key=lambda x: os.path.getmtime(os.path.join(graveyard_path, x)))
                    os.remove(os.path.join(graveyard_path, files_in_graveyard[0]))
        else:
            click.echo(f"Your fireball fizzles... The target at {file_path} does not exist. Even in the arcane arts, one cannot destroy what is already absent.")

alias = "fb"

def main():
    fireball() 

if __name__ == "__main__":
    main()