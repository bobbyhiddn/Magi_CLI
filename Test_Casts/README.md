# Test_Casts

This directory contains test files and examples for the Magi CLI spell system, demonstrating various spell types and their proper structure.

## Directory Structure

```
Test_Casts/
├── bundled_spells/           # Complex multi-file spells
│   ├── runecraft.spell/      # Example: Rune generation spell
│   ├── weather.spell/        # Example: Weather checking spell
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
│   └── [resource files]    # Configs, data files, etc.
└── spell/                  # Core spell files
    ├── spell.yaml          # Spell metadata
    └── spell_name.py       # Main spell code
```

Example spell.yaml:
```yaml
description: What the spell does
entry_point: spell/spell_name.py
name: spell_name
shell_type: python
type: bundled
version: 1.0.0
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
# Cast a bundled spell
cast spell_name.spell

# Cast an integrated spell
cast spell_name
```

### Spell Structure Requirements

1. **Bundled Spells**:
   - Main code goes in `spell/spell_name.py`
   - Configuration in `spell/spell.yaml`
   - Resources/dependencies in `artifacts/`
   - Entry point must be relative to spell root (e.g., `spell/spell_name.py`)

2. **YAML Recipes**:
   - Must include all required metadata
   - Code is embedded in the YAML file

3. **Direct Scripts**:
   - Must be executable
   - Should include proper shebang line