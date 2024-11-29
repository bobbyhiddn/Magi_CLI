# Spellcraft (sc)

## Overview
The Spellcraft spell enables the creation of macro spells by combining multiple commands into a single executable spell file. It's perfect for automation and workflow optimization.

## Features
- Command sequencing
- Spell file generation
- Description storage
- Command verification
- Persistent storage

## Requirements
- Python package: `click`

## Installation
```bash
cast ponder spellcraft
```

## Usage
```bash
cast sc <number_of_commands> <spell_name>
```

## Storage Location
Spell files are stored in `~/.sanctum/.tome/`

## Examples

### Creating a Simple Spell
```bash
cast sc 3 backup_project
Enter a description for the macro spell: Backup project files and clean directory
Enter command 1: git add .
Enter command 2: git commit -m "Backup $(date)"
Enter command 3: git push origin main
```

### Using the Created Spell
```bash
cast backup_project
```

## Spell File Format
```
# Description: <spell_description>

<command1>
<command2>
<command3>
...
```

## Common Use Cases
1. Git workflows
2. Build processes
3. Backup routines
4. System maintenance
5. Development tasks

## Best Practices
- Use descriptive spell names
- Add clear descriptions
- Test commands individually
- Verify command sequence
- Document dependencies

## Command Guidelines
- Use absolute paths when needed
- Consider environment variables
- Check command dependencies
- Verify command permissions
- Test error conditions

## Features in Detail

### Description Storage
- Markdown compatible
- Command documentation
- Usage instructions
- Dependency notes

### Command Processing
- Sequential execution
- Error handling
- Path resolution
- Variable expansion

### Storage Management
- Organized directory structure
- Consistent naming
- Version tracking
- Backup support

## Technical Notes
- Commands run sequentially
- Environment preserved
- Directory awareness
- Error propagation
- State persistence

## Tips
1. Plan command sequence
2. Test commands first
3. Use descriptive names
4. Document requirements
5. Verify permissions