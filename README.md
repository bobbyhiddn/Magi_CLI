## Magi CLI: An Esoteric Command Line Tool

![banner](MAGI_Keys.png)


Embrace the arcane with Magi CLI, a spellcasting-inspired command line interface (CLI) tool that fuses the mystical arts with practical utility. Unravel the secrets of the cosmos and command your operating system with the wisdom of the ancient magi.

### Overview

Magi CLI is forged in Python, channeling the enigmatic power of the Click library. It offers an array of spells (commands) that manipulate the filesystem, manage files, and automate tasks. Designed to be extendable, Magi CLI allows you to add new spells as your knowledge of the hidden arts expands. It was also designed to be platform agnostic, but it should be used with a bash terminal like Git Bash for best performance. Use of Magi_CLI should empower the user, not remind them of the current in-sufficiently advanced software. Because remember Clarke's third law:

**Any sufficiently advanced technology is indistinguishable from magic.**

### Cast

This is the root command. It is the main entry point that binds all the other spells together and conjures the CLI. It is the first spell you should cast when using the CLI. It is also the spell that allows you to cast other spells. When you use `cast` it will display all available spells and .spell files in your tome. The .spell files will be listed from your default tome path set with the `TOME_PATH` variable or if that is not set, the .spell files in the .tome folder in your current directory will be listed. 

Another goal for cast is to serve as a universal execution command. I despise having to use python or bash as prefixes to run a file, so I want to be able to execute most files with cast. Currently cast supports .py, .sh, and .spell files. I want to add support for .exe, .jar, and other files as well in the future.

#### Spells (Commands)

##### Tenets

Spells are designed with a few things in mind:

- Effectiveness - They need to work. Half functioning spells won't be included in a release version.
- Flavorfulness - They need to feel like magic. They should work in a manner that does not require memorization besides magic words and a target unless a flavorful way to add more features can be devised.
- Modulararity - They need to fit into Magi_CLI in a fully functional way. If you can't both cast it with `cast spell target` or `python path/to/spell.py target`, it is not acceptable. Each command should be both executable and castable as both file and command.
- Innovative - A spell will not be accepted if it only performs a task that a UNIX command already performs. We're crafting spells here, not reworking old ground.
- Fun! - They should be enjoyable to use! Keep the debug messages in theme, keep the soul of the project alive!

##### Current Spells

1. **Fireball**: ('**fb**') Transmute a file or directory into ashes, sending it to the '.graveyard' realm. This command deletes a file or directory and moves it to the '.graveyard' directory, ensuring that the deleted files are preserved in case they need to be restored later.

2. **Necromancy**: ('**nc**') Conjure a '.graveyard' domain to preserve the spirits of deleted files. This command creates a '.graveyard' directory, which serves as a storage location for deleted files. (I want to add more functionality to this command)

3. **Ponder**: ('**pd**') Ponder your `.orb` and the Chamber to gain insight into available spells both locally and in the astral plane. This command allows you to:

   - **List Spells**: Display all available spells from both your local orb and the remote Chamber.
   - **Learn Spells**: Fetch new spells from the Chamber and install them into your local spells directory. Spells are managed from `https://github.com/bobbyhiddn/Magi.Spells` and are synced automatically to Magi.Chamber(`magi-chamber.fly.dev`).
   - **Unlearn Spells**: Remove spells from your local spells directory and your orb.
   - **Synchronize Spells**: Sync your local orb with the Chamber to ensure you have the latest versions of spells.
   - **Relearn Spells**: Reinstall spells from your orb that are missing in your spells directory. This allows you to recover spells after a reinstallation or migration by just migrating your .sanctum directory.

4. **Divine**: ('**dv**') Gaze into the astral plane to unveil the contents and attributes of a file or directory. This command lists the contents of a directory with detailed information, such as file size, permissions, and last modified date.

5. **Raise_Dead**: ('**rd**') Commune with the spirits in the '.graveyard' and restore them to the material plane if desired. This command lists all files in the '.graveyard' directory and allows you to restore them if desired.

6. **Spellcraft**: ('**sc**') Weave multiple commands into a powerful macro spell, inscribing it in '.spell' scrolls. The commands are saved in the order they were channeled and can be executed in sequence. These spells are then recorded in a .tome directory within your .sanctum folder.

7. **Runecraft**: ('**rc**') Craft a rune through the power of sigaldry enchanted with a single spell. Creates a button GUI with PyQT5 that can be used to execute a spell, bash, or python file. The image for the rune is generated with DALL-E, so the OPENAI_API_KEY environment variable must be set. This might be my favorite spell. The purpose of this is to have an easy way to repeat a command or script in an efficient way without having to schedule it with Unseen_Servant or type out the command every time. The GUI is also independant from the terminal in that it won't interfere with your other commands, but the execution of the file is run from the terminal the GUI was created on and when that terminal is closed, it will shut down the GUI.

8. **Aether_Inquiry**: ('**ai**') Seek answers from an AI oracle like GPT-4. This will default to calling the GPT-4 API. This command will allow you to generate code to .spell files or ask questions about code, files, or even entire folders. If you give it a file argument, it will read the file provided and allow you to discuss it. If you don't provide a file, it will default to discussing code and will generate code for you to use in a .spell, .py, .bash, or .txt file by saying `scribe` during the conversation. If you provide a folder, it will offer to transcribe the contents into one file in a .aether directory and allow you to converse with the contents of the entire folder! It also gives you the option to save the conversation to a markdown file and pick it up at a later date by typing `quit` during the conversation. 
   - Adding local LLM functionality soon!

9. **Exile**: ('**ex**') Banish a file or directory to the /tmp or C:\temp directory in a realm called .exile. This allows for the removal of a file from your root directory without getting rid of it completely.

10. **Warp**: ('**wp**') Warp to remote SSH sessions with ease. This command allows you to manage and connect to SSH sessions effortlessly. It provides a user-friendly interface to register new SSH sessions, edit existing ones, and quickly connect to them. With Warp, you can:
   - List all registered SSH sessions
   - Choose a session to connect to
   - Add a new SSH session by providing the host, username, and optional private key
   - Generate a new RSA key pair for authentication or use an existing private key
   - Delete an existing SSH session and its associated keys
   - Directly connect to a session using its alias

11. **Scribe**: ('**sb**') Transcribe the contents of a file or directory into markdown format. This spell captures the essence of your chosen realm, preserving its knowledge in a format easily understood by both mortal and magical beings. You can choose to include or exclude .git directories, and decide whether to etch your transcriptions into the aether (.aether folder in your sanctum) or keep them in the mortal realm (current directory).

12. **Pagecraft**: ('**pgc**') Transform web pages into markdown documents through aether inquiry (AI). This spell fetches content from a URL, uses AI to convert it into well-formatted markdown, and saves it locally. Features include:
   - Intelligent content extraction and formatting
   - Multiple review and improvement passes
   - AI-generated filenames
   - Configurable save location via SCRAPE_ARCHIVE_PATH
   - Quality rating and final review

##### Future Spells

1. **Unseen_Servant**: ('**uss**') Enlist an ethereal ally to cast spells at regular intervals. Can invoke any '.spell' scroll on a schedule. This command schedules a spell to be cast on a regular basis, allowing you to automate tasks by running any '.spell' file on a schedule. (WIP)
2. **Astral_Realm**: ('**ar**') This would be a remote repository that stores your spells from your tome directory. This would allow you to share spells with other users and have a backup of your spells in case your tome is lost. (WIP)

### Usage

To wield the Magi CLI without invoking 'python magi_cli.py', install it with pip:

#### Locally

```
pip install .
```

#### Or From PyPi

```
pip install magi-cli-pypi
```
#### Now Spellcast!

Simply utter the spell name and the required incantations to harness its power:

Example:

```
cast fireball test.py
```

or cast with its alias:

```
cast fb test.py
```

### Future Enchantments

Additional spells, file type support, and arcane features can be added to the CLI based on the desires and whims of its practitioners. Beware that some spells (Astral_Realm, Unseen_Servant) are not fully defined yet, and their arcane secrets may change.

#### Spell Ideas

**Astral Realm** - This would be a remote repository that stores your spells from your tome directory 

#### Spell Improvements

- Spellcraft: Allow the use of arcane variables in '.spell' scrolls for more dynamic spell weaving. I want spellcraft to be a versatile tool that can be used to accomplish more than just basic tasks without having to go too far into specifics on the users side. I'd like to eventually design a 'recording' system that can remember your last few commands.

- Runecraft: Implement a way to save runes to a tome directory and allow them to be executed from the CLI. Allow runes to be saved as .spell files. Something like that.

- Astral_Realm: We need to figure out if flask is all we need backend wise. Also looking into FastUI and FastAPI.

#### General Improvements

- I would like to have more flavorful errors and responses to commands when using the CLI.
- I need to find a better way to include aliases
- I need to figure out if click is the best library to move forward with.

### Future Plans

1. **The Astral Realm of Formulas** - This is both the public spell repo and the community forum for discussing the future of MAGI_CLI. This has been partially accomplished in the form of Magi.Chamber, but I want to expand on this idea and make it a more interactive experience. I want to have a forum where users can discuss the future of the project and submit their own spells. I want to have a way to vote on spells and contribute to the future of the project.

2. **MAGI_CLI Sanctum** - This is an IDE for MAGI_CLI that responds to casting spells and creating commands with animations and sound effects. It will have the same goal as the CLI itself, which is to both have fun functionality and to supercharge your terminal experience.

3. **MAGI_CLI VSCode Extension** - This will be an extension that allows you to have the fun and functionality of MAGI_CLI in VSCode. I want to incorporate the animations and sound effects from the Sanctum into this extension.

### Contributing

If you would like to contribute to the project, please read the [CONTRIBUTING.md](CONTRIBUTING.md) file for more information.