# Magi CLI: A Wizard-Themed Command Line Tool 

Magi CLI is a fun, wizard-themed command line interface (CLI) that combines utility and fantasy aesthetics. The goal of this tool is to make interacting with your operating system feel magical and efficient.

## Overview

Magi CLI is implemented in Python, using the Click library. It provides a variety of 'spells' (commands) that perform operations on the filesystem, manage files, and automate tasks. It is designed to be extendable, allowing for the addition of new spells as needed.

## Spells (Commands)

- **Fireball**: Recursively delete a file or directory, then move it into a '.graveyard' directory.
- **Necromancy**: Create a '.graveyard' directory to store deleted files.
- **Divine**: Display all contents and attributes of a file or directory.
- **Raise_Dead**: List all files in the '.graveyard' directory and restores them if desired.
- **Enchant**: Convert a file to a different file type. (Details to be defined)
- **Cast**: Execute a file based on its extension. Supports Python and Bash scripts.
- **Prestidigitation**: Generate content in a file or provide a response using an AI model like GPT-4. (Details to be defined)
- **Spellcraft**: Macro multiple commands and register them in '.spell' files. The commands are saved in the order they were input and can be executed in sequence.
- **Unseen_Servant**: Schedule spells to be cast at regular intervals. Can run any '.spell' file on a schedule.

## File Structure

- **cast.py**: Main script that adds all the commands and starts the CLI.
- **spells.py**: Contains the implementation of all the commands.

## Usage

Magi CLI can be run without prefacing each command with 'python magi_cli.py'. Just enter the spell name and the required arguments to use it.

Example:

```bash
cast fireball test.py
```

## Future Extensions

Additional spells, file type support, and features can be added to the CLI based on user needs and preferences.

---

Please note that some spells (Spellcraft, Unseen_Servant) are not fully defined yet and their implementation details are subject to change.

