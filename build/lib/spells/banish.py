import click
import os
import shutil

@click.command()
@click.argument('spell_file', required=True)
def banish(spell_file):
    '''Banish a target to the /tmp directory in a .exile folder. If no /tmp directory exists, place it in a C:\\temp\.exile directory.'''
    # Check if /tmp exists
    if os.path.exists("/tmp"):
        exile_dir_unix = "/tmp/.exile"
        if not os.path.exists(exile_dir_unix):
            os.mkdir(exile_dir_unix)
        shutil.move(spell_file, os.path.join(exile_dir_unix, os.path.basename(spell_file)))
        click.echo(f"Spell {spell_file} has been banished to the /tmp directory in a .exile folder.")
    else:
        exile_dir_win = "C:\\temp\\.exile"
        if not os.path.exists(exile_dir_win):
            os.mkdir(exile_dir_win)
        shutil.move(spell_file, os.path.join(exile_dir_win, os.path.basename(spell_file)))
        click.echo(f"{spell_file} has been banished to the C:\\temp directory in a .exile folder.")