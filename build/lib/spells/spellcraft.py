import click
import os

@click.command()
@click.argument('num_commands', type=int, required=True)
@click.argument('spell_file', required=True)
def spellcraft(num_commands, spell_file):
    """Create a macro spell and store it in .tome."""
    default_tome_dir = os.getenv("TOME_PATH")  # Get default .tome location from environment variable
    tome_dir = default_tome_dir if default_tome_dir else ".tome"  # Use .tome in current directory if default location is not set

    if not os.getenv('TOME_PATH'):
        os.environ['TOME_PATH'] = input('Please set your TOME_PATH environmental variable or Magi_CLI will default to a .tome folder in your local directory. Press enter to continue.')
        pass

    # If .tome directory does not exist, create it
    if not os.path.exists(tome_dir):
        os.mkdir(tome_dir)

    # Prompt the user for a description
    description = click.prompt("Enter a description for the macro spell")

    # Create a list to store the entered commands
    entered_commands = []

    # Prompt the user to enter the desired commands
    for i in range(num_commands):
        entered_command = input(f"Enter command {i + 1}: ")
        entered_commands.append(entered_command)

    # Write the description and entered commands to the specified spell_file in the .tome directory
    spell_file_path = os.path.join(tome_dir, f"{spell_file}.spell")
    with open(spell_file_path, 'w') as f:
        f.write(f"# Description: {description}\n\n")
        for command in entered_commands:
            f.write(f"{command}\n")

    click.echo(f"Macro spell created and stored in {spell_file_path}")