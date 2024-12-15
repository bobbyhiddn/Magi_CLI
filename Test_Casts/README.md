# Test_Casts

This directory contains test files and examples for the Magi CLI spell system, demonstrating various spell types and their proper structure.

## Directory Structure

```
Test_Casts/
├── bundled_spells/           # Complex multi-file spells
│   ├── runecraft.spell/      # Example: Rune generation spell
│   ├── counter.spell/        # Example: Word frequency counter
│   ├── sentiment.spell/      # Example: Text sentiment analyzer
│   └── greetings.spell/      # Example: Multi-language greetings
├── yaml_spell_recipes/       # YAML-based spell definitions
└── py_test.py, sh_test.sh   # Simple script spells
```

## Spell Types

### 1. Bundled Spells
Located in `bundled_spells/`, these are complex spells that may require multiple files or external resources.

Structure:
```
spell_name.spell/
├── artifacts/               # Resources and dependencies
│   └── [resource files]    # Data files, configs, etc.
└── spell/                  # Core spell files
    ├── spell.yaml          # Spell metadata and requirements
    └── spell_name.py       # Main spell code
```

Example spell.yaml:
```yaml
description: Analyze sentiment in text using TextBlob
entry_point: spell/analyzer.py
name: sentiment
shell_type: python
type: bundled
version: 1.0.0
requires:
  - textblob>=0.17.1        # Required packages are auto-installed
```

### 2. YAML Recipe Spells
Located in `yaml_spell_recipes/`, these are single-file spells defined in YAML format.

### 3. Direct Scripts
Simple single-file spells:
- Python scripts (`.py`)
- Shell scripts (`.sh`)

## Usage

### Casting Spells

```bash
# Cast a bundled spell (dependencies are auto-installed)
cast spell_name.spell

# Cast an integrated spell
cast spell_name

# Examples:
cast sentiment.spell                    # Uses sample positive text
cast sentiment.spell my_text_file.txt   # Analyzes custom text file
```

### Spell Structure Requirements

1. **Bundled Spells**:
   - Main code goes in `spell/spell_name.py`
   - Configuration in `spell/spell.yaml`
   - Resources/dependencies in `artifacts/`
   - Entry point must be relative to spell root (e.g., `spell/spell_name.py`)
   - Python packages in `requires` field are automatically installed

2. **YAML Recipes**:
   - Must include all required metadata
   - Code is embedded in the YAML file

3. **Direct Scripts**:
   - Must be executable
   - Should include proper shebang line

### Dependency Management

Bundled spells can specify required Python packages in their `spell.yaml`:
```yaml
requires:
  - package_name>=1.0.0    # Will be installed automatically
  - another_package~=2.0   # Supports standard version specifiers
```

When casting a spell, any missing dependencies are automatically installed into an isolated environment, ensuring:
1. No conflicts with other spells or system packages
2. Correct versions are used
3. Clean environment for each spell execution