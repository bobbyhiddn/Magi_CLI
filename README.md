## Magi CLI: An Esoteric Command Line Tool

![banner](MAGI_Keys.png)


Embrace the arcane with Magi CLI, a spellcasting-inspired command line interface (CLI) tool that fuses the mystical arts with practical utility. Unravel the secrets of the cosmos and command your operating system with the wisdom of the ancient magi.

### Overview

Magi CLI is forged in Python, channeling the enigmatic power of the Click library. It offers an array of spells (commands) that manipulate the filesystem, manage files, and automate tasks. Designed to be extendable, Magi CLI allows you to add new spells as your knowledge of the hidden arts expands. It was also designed to be platform agnostic, but it should be used with a bash terminal like Git Bash for best performance. 


### Cast

This is the root command. It is the main entry point that binds all the other spells together and conjures the CLI. It is the first spell you should cast when using the CLI. It is also the spell that allows you to cast other spells. When you use `cast` it will display all available spells and .spell files in your tome. The .spell files will be listed from your default tome path set with the `TOME_PATH` variable or if that is not set, the .spell files in the .tome folder in your current directory will be listed. 

Another goal for cast is to serve as a universal execution command. I despise having to use python or bash as prefixes to run a file, so I want to be able to execute most files with cast. Currently cast supports .py, .sh, and .spell files. I want to add support for .exe, .jar, and other files as well in the future.

#### Spells (Commands)

1. **Fireball**: Transmute a file or directory into ashes, sending it to the '.graveyard' realm. This command deletes a file or directory and moves it to the '.graveyard' directory, ensuring that the deleted files are preserved in case they need to be restored later.

2. **Necromancy**: Conjure a '.graveyard' domain to preserve the spirits of deleted files. This command creates a '.graveyard' directory, which serves as a storage location for deleted files. (I want to add more functionality to this command)

3. **Divine**: Gaze into the astral plane to unveil the contents and attributes of a file or directory. This command lists the contents of a directory with detailed information, such as file size, permissions, and last modified date.

4. **Raise_Dead**: Commune with the spirits in the '.graveyard' and restore them to the material plane if desired. This command lists all files in the '.graveyard' directory and allows you to restore them if desired.

5. **Enchant**: Transform a file into a different file type. (WIP)

6. **Spellcraft**: Weave multiple commands into a powerful macro spell, inscribing it in '.spell' scrolls. The commands are saved in the order they were channeled and can be executed in sequence. These spells are then recorded in a .tome directory.

7. **Conjure**: Create a new file or directory. This command creates a new file or directory in the current directory. (WIP)

8. **Runecraft**: Craft a rune through the power of sigaldry enchanted with a single spell. Creates a button GUI with PyQT5 that can be used to execute a spell, bash, or python file. The image for the rune is generated with DALL-E, so the OPENAI_API_KEY environment variable must be set. This might be my favorite spell. The purpose of this is to have an easy way to repeat a command or script in an efficient way without having to schedule it with Unseen_Servant or type out the command every time. The GUI is also independant from the terminal in that it won't interfere with your other commands, but the execution of the file is run from the terminal the GUI was created on and when that terminal is closed, it will shut down the GUI.

9.  **Unseen_Servant**: Enlist an ethereal ally to cast spells at regular intervals. Can invoke any '.spell' scroll on a schedule. This command schedules a spell to be cast on a regular basis, allowing you to automate tasks by running any '.spell' file on a schedule. (WIP)

10. **Aether_Inquiry**: Seek answers from an AI oracle like GPT-4. This will default to calling the GPT-4 API. This command will allow you to generate code to .spell files or ask questions about code or files. If you give it a file argument, it will read the file provided and allow you to discuss it. If you don't provide a file, it will default to discussing code and will generate code for you to use in a .spell, .py, .bash, or .txt file by saying 'scribe' during the conversation.

11. **Exile** - Banish a file or directory to the /tmp or C:\temp directory in a realm called .exile. This allows for the removal of a file from your root directory without getting rid of it completely.

### Grimoire Structure

- **cast.py**: The main scroll that binds all the spells and conjures the CLI.
- **setup.py**: A ritual to install the CLI with pip and invoke it with the command `cast`.

### Usage

To wield the Magi CLI without invoking 'python magi_cli.py', install it with pip:

```
pip install .
```

Simply utter the spell name and the required incantations to harness its power:

Example:

```
cast fireball test.py
```

### Future Enchantments

Additional spells, file type support, and arcane features can be added to the CLI based on the desires and whims of its practitioners. Beware that some spells (Spellcraft, Unseen_Servant) are not fully defined yet, and their arcane secrets may change.

#### Spell Ideas

**Astral Realm** - This would be a remote repository that stores your spells from your tome directory 

#### Spell Improvements

- Spellcraft: Allow the use of arcane variables in '.spell' scrolls for more dynamic spell weaving. Also, remove the need to specify the path to the '.tome' realm if no path is provided.

- Runecraft: Add a flag that specifies whether the rune will always run from the directory you created it in(This is how it currently functions) or will execute the file in the directory you are currently in when you run the rune. This will allow you to create a rune in one directory and then use it in another directory without having to create a new rune and to the same effect. 

#### General Improvements

I would like to have more flavorful errors and responses to commands when using the CLI.

### Future Plans

1. **The Astral Realm of Formulas** - This is both the public spell repo and the community forum for discussing the future of MAGI_CLI. 

2. **MAGI_CLI Sanctum** - This is an IDE for MAGI_CLI that responds to casting spells and creating commands with animations and sound effects. It will have the same goal as the CLI itself, which is to both have fun functionality and to supercharge your terminal experience.

3. **MAGI_CLI VSCode Extension** - This will be an extension that allows you to have the fun and functionality of MAGI_CLI in VSCode. I want to incorporate the animations and sound effects from the Sanctum into this extension.
