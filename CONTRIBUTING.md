# Contributing to Magi CLI

Thank you for your interest in contributing to Magi CLI! We welcome contributions from the community to enhance the functionality and expand the collection of spells available in Magi CLI.

## Spell Format and Location

To ensure that your spells function seamlessly with the `cast` command and maintain consistency within the Magi CLI project, please follow these guidelines when creating new spells:

- **Location**: Spells should be located in the `./magi_cli/spells/` directory. This is the default location where the `cast` command looks for spells.
- **File Name**: Each spell should have its own Python file with a descriptive name. For example, `fireball.py`, `warp.py`, etc.
- **Spell Structure**: Spells should be structured as Python scripts that can be executed independently. They should have a `main` function that serves as the entry point for the spell when executed directly.
- **Alias**: Every spell should have an alias defined at the bottom of the file, just above the `if __name__ == '__main__':` block. The alias is a short, memorable name for the spell that can be used with the `cast` command. For example: `alias = "fb"` for the fireball spell.
- **Execution**: Spells should be executable both through the `cast` command and as individual scripts using `python magi_cli/spells/fireball.py target`. This allows users to run the spells directly if needed.
- **Click Integration**: Spells should use the `click` library for command-line parsing and argument handling. This ensures consistency with the existing spells and allows for easy integration with the `cast` command.
- **Documentation**: Each spell should have a docstring at the top of the file that describes its purpose, usage, and any required arguments or options. This helps users understand how to use the spell effectively.
- **Error Handling**: Spells should include appropriate error handling and provide informative error messages to guide users when something goes wrong.
- **Naming Conventions**: Spell names should follow the naming conventions of the Magi CLI project. Use lowercase with underscores for file names and function names, and capitalize the first letter of each word for class names.
- **DO NOT CHANGE CAST.PY**: Do not modify the `cast.py` file directly. If you need to make changes to the `cast` command or its behavior, open an issue to discuss your proposed changes.

## Spell Ideas

If you have ideas for new spells that you think would be valuable additions to Magi CLI, please open an issue on the project's repository. Describe your spell idea, its purpose, and any specific requirements or considerations. The project maintainers will review your suggestion and provide feedback.

## Pull Requests

If you have implemented a new spell or made improvements to existing ones, you can submit a pull request to have your changes reviewed and merged into the main project. Here are the steps to create a pull request:

1. Fork the Magi CLI repository to your own GitHub account.
2. Create a new branch for your changes: `git checkout -b my-new-spell`.
3. Implement your spell or make the necessary changes in the appropriate files.
4. Test your changes thoroughly to ensure they work as expected and don't introduce any regressions.
5. Commit your changes with descriptive commit messages: `git commit -m "Add new spell: My Amazing Spell"`.
6. Push your changes to your forked repository: `git push origin my-new-spell`.
7. Open a pull request on the main Magi CLI repository, providing a clear description of your changes and any relevant information.
8. The project maintainers will review your pull request, provide feedback if necessary, and merge your changes if they align with the project's goals and guidelines.

Thank you for contributing to Magi CLI and helping to expand the realm of arcane computing!