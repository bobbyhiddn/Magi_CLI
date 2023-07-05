#!/usr/bin/env python3

import click
from .spells import *

@click.group()
def cli():
    pass

cli.add_command(fireball)
cli.add_command(necromancy)
cli.add_command(raise_dead)
cli.add_command(divine)
cli.add_command(enchant)
cli.add_command(spellcraft)
cli.add_command(unseen_servant)
cli.add_command(ponder)

# Add commands with aliases
cli.add_command(fireball, name='fb')
cli.add_command(necromancy, name='ncr')
cli.add_command(raise_dead, name='rd')
cli.add_command(divine, name='dv')
cli.add_command(enchant, name='enc')
cli.add_command(spellcraft, name='spc')
cli.add_command(unseen_servant, name='uss')
cli.add_command(ponder, name='pn')


if __name__ == "__main__":
    cli()
