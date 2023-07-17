import click
import inspect
import os
import sys
import glob

@click.command()
@click.argument('file', required=False)
def ponder(file):
    """Ponders a specific file or all spells in the .orb directory."""
    orb_dir = ".orb"

    # If .orb directory does not exist, create it
    if not os.path.exists(orb_dir):
        os.mkdir(orb_dir)

    if file:
        # If a file argument was supplied, check if it exists in the current directory
        if os.path.exists(file):
            with open(file, 'r') as f:
                print(f.read())
        else:
            # If it doesn't exist in the current directory, check the .orb directory
            file_path = os.path.join(orb_dir, f"{file}.spell")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    print(f.read())
            else:
                print(f"File {file} does not exist in current directory or .orb directory.")
    else:
        # If no file argument was supplied, generate spell files as before
        all_spells = [member for name, member in inspect.getmembers(sys.modules[__name__]) if isinstance(member, click.core.Command)]
        for spell in all_spells:
            spell_file = os.path.join(orb_dir, f"{spell.name}.spell")
            if not os.path.exists(spell_file):
                doc = inspect.getdoc(spell)
                if doc is not None:
                    with open(spell_file, 'w') as f:
                        f.write("# " + doc.replace('\n', '\n# ') + "\n")
                        f.write("# Source code:\n")
                        f.write(click.formatting.wrap_text(spell.callback.__doc__))
                        f.write("\n")
                        f.write(click.formatting.wrap_text(inspect.getsource(spell.callback)))

        # List all the .spell files in the .orb directory
        spell_files = glob.glob(os.path.join(orb_dir, "*.spell"))
        files = [os.path.splitext(os.path.basename(f))[0] for f in spell_files]
        if files:
            click.echo("You ponder the orb. Runic glyphs expand in the vortices. Your mind fills with knowledge of the arcane:")
            for file in files:
                click.echo(file)
            spell_name_to_ponder = click.prompt("Which spell would you like to ponder?", type=str)
            spell_file_path = os.path.join(orb_dir, f"{spell_name_to_ponder}.spell")
            if os.path.exists(spell_file_path):
                with open(spell_file_path, 'r') as f:
                    click.echo(f.read())
            else:
                click.echo(f"Spell {spell_name_to_ponder} does not exist in the .orb directory.")
        else:
            click.echo("No magics were found in your orb.")
