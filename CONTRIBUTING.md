# Contributing to Magi CLI

Thank you for your interest in contributing to Magi CLI! We welcome contributions from the community to enhance the functionality and expand the collection of spells available in Magi CLI.

## Spell Format and Location

To ensure that your spells function seamlessly with the `cast` command and maintain consistency within the Magi CLI project, please follow these guidelines when creating new spells:

- **Location**: While testing, should be located in the `./magi_cli/spells/` directory. This is the default location where the `cast` command looks for spells. Once they have been thoroughly tested and vetted by repo owners, they will be migrated to the Magi.Spells repo(`https://github.com/bobbyhiddn/Magi.Spells`)

- **File Name**: Each spell should have its own Python file with a descriptive and thematic name. For example, `fireball.py`, `warp.py`, etc.

- **Spell Structure**: Spells should be structured as Python scripts that can be executed independently. They should have a `main` function that serves as the entry point for the spell when executed directly.

- **Alias**: Every spell should have an `alias` variable defined in the script. This alias is a short, memorable name for the spell that can be used with the `cast` command. For example: `alias = "fb"` for the fireball spell.

- **Execution**: Spells should be executable both through the `cast` command and as individual scripts using `python magi_cli/spells/fireball.py target`. This allows users to run the spells directly if needed.

- **Click Integration**: Spells should use the `click` library for command-line parsing and argument handling. This ensures consistency with the existing spells and allows for easy integration with the `cast` command.

- **Per-Spell Dependencies**:

  - **Declare Dependencies**: Each spell should declare its external dependencies using a special `__requires__` variable within the spell script. This variable is a list of packages that are not part of Python's standard library but are required for the spell to function.

    ```python
    __requires__ = ['click', 'requests', 'openai']
    ```

  - **Dependency Management**: The `ponder` command handles the installation of these dependencies when the spell is installed. Ensure that all necessary dependencies are included in the `__requires__` list.

  - **Version Specifiers**: If your spell requires specific versions of packages, include version specifiers in the `__requires__` list.

    ```python
    __requires__ = ['click>=7.0', 'openai==0.6.0']
    ```

- **Documentation**:

  - **Module Docstring**: Include a docstring at the top of the file that describes the spell's purpose and usage.

  - **Function Docstring**: The main spell function should have a docstring that provides details on arguments, options, and any other relevant information.

- **Error Handling**: Spells should include appropriate error handling and provide informative error messages to guide users when something goes wrong.

- **Naming Conventions**: Follow Python's naming conventions:

  - Use lowercase with underscores for file names and function names (e.g., `fireball.py`, `def cast_fireball():`).

  - Capitalize class names using CamelCase (e.g., `class FireballSpell:`).

- **DO NOT CHANGE `cast.py` or `__init__.py`**:

  - Do not modify the `cast.py` or `__init__.py` files directly. Command registrations are handled centrally.

  - If you need to make changes to the core functionality, open an issue to discuss your proposed changes.

## Spell Ideas

If you have ideas for new spells that you think would be valuable additions to Magi CLI, please open an issue on the project's repository. Describe your spell idea, its purpose, and any specific requirements or considerations. The project maintainers will review your suggestion and provide feedback.

## Pull Requests

If you have implemented a new spell or made improvements to existing ones, you can submit a pull request to have your changes reviewed and merged into the main project. Here are the steps to create a pull request:

1. **Fork the Repository**: Fork the Magi CLI repository to your own GitHub account.

2. **Create a New Branch**: Create a new branch for your changes:

   ```bash
   git checkout -b my-new-spell
   ```

3. **Implement Your Spell**:

   - Add your spell script to the `magi_cli/spells/` directory.

   - Ensure your spell follows the guidelines outlined above.

4. **Test Your Changes**:

   - Use the `ponder` command to install your spell and verify that dependencies are correctly managed.

   - Test your spell thoroughly to ensure it works as expected and doesn't introduce any regressions.

5. **Commit Your Changes**:

   ```bash
   git commit -m "Add new spell: My Amazing Spell"
   ```

6. **Push Your Changes**:

   ```bash
   git push origin my-new-spell
   ```

7. **Open a Pull Request**:

   - Open a pull request on the main Magi CLI repository.

   - Provide a clear description of your changes and any relevant information.

8. **Review Process**:

   - The project maintainers will review your pull request.

   - They may provide feedback or request changes.

   - Once approved, your changes will be merged into the main project.

## Contribution Guidelines

- **Code Style**:

  - Follow Python best practices and [PEP 8](https://www.python.org/dev/peps/pep-0008/) guidelines.

  - Keep your code clean and well-documented.

- **Dependencies**:

  - Only include necessary external dependencies.

  - Use standard library modules whenever possible.

  - Ensure all external dependencies are declared in the `__requires__` variable.

- **Error Handling**:

  - Ensure your spell handles errors gracefully.

  - Provide meaningful error messages to the user.

- **Testing**:

  - Thoroughly test your spell in various scenarios.

  - Verify that dependencies are properly declared and installed.

- **Licensing**:

  - By contributing, you agree that your contributions will be licensed under the same license as this repository (MIT License).

## Reporting Issues

If you encounter any issues or have suggestions for improvements, please open an issue on the GitHub repository. Provide as much detail as possible to help us address the problem.

Thank you for contributing to Magi CLI and helping to expand the realm of arcane computing!