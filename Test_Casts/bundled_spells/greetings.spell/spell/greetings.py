import json
from pathlib import Path

def main():
    # Load greetings from the JSON file in artifacts
    spell_dir = Path(__file__).parent.parent
    with open(spell_dir / "artifacts" / "greetings.json", "r") as f:
        greetings = json.load(f)
    
    # Print each greeting
    for lang, greeting in greetings.items():
        print(f"{lang}: {greeting}")

if __name__ == "__main__":
    main()
