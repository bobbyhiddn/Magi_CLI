import click
import os
import shutil

@click.command()
@click.argument('path', required=True)
def fireball(path):
    """Deletes a directory or file."""
    graveyard_path = ".graveyard"
    if os.path.exists(path):
        click.echo(f"Your hands tremble as you draw upon the arcane energies...\n")

        # Check whether the path is a file or a directory
        if os.path.isfile(path):
            confirmation_prompt = "Are you sure you want to continue? A target sent to the graveyard is as dead as can be."
        elif os.path.isdir(path):
            confirmation_prompt = "You are about to incinerate a directory and everything within it, sending it to the graveyard. Are you sure you want to continue?"
        else:
            confirmation_prompt = "Are you sure you want to continue? A target sent to the graveyard is as dead as can be."
        
        if click.confirm(confirmation_prompt, abort=True):
            click.echo("You cast the spell and a fireball erupts from your hands, engulfing the target in flames...")
            click.echo("When the smoke clears, nothing remains but cinder and ash.")
            destination_path = os.path.join(graveyard_path, os.path.basename(path))
            shutil.move(path, destination_path)

            # Clean up the graveyard if it has more than 13 files
            files_in_graveyard = os.listdir(graveyard_path)
            if len(files_in_graveyard) > 13:
                files_in_graveyard.sort(key=lambda x: os.path.getmtime(os.path.join(graveyard_path, x)))
                os.remove(os.path.join(graveyard_path, files_in_graveyard[0]))
    else:
        click.echo(f"Your fireball fizzles... The target at {path} does not exist. Even in the arcane arts, one cannot destroy what is already absent.")