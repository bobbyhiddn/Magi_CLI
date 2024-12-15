#!/usr/bin/env python3
import click
import json
from collections import Counter
from pathlib import Path

@click.command()
@click.argument('text_file', type=click.Path(exists=True), required=False)
@click.option('--top', '-n', default=10, help='Number of top words to show')
def main(text_file, top):
    """Count word frequencies in a text file. If no file is specified, uses the sample text."""

    # Get spell directory
    spell_dir = Path(__file__).parent.parent

    # Use sample.txt if no file specified
    if text_file is None:
        text_file = str(spell_dir / 'artifacts' / 'sample.txt')

    # Read the text file
    with open(text_file, 'r', encoding='utf-8') as f:
        text = f.read().lower()

    # Load stop words from artifacts
    stop_words_path = spell_dir / 'artifacts' / 'stop_words.json'
    
    with open(stop_words_path, 'r', encoding='utf-8') as f:
        stop_words = set(json.load(f))

    # Split into words and remove punctuation
    words = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in text).split()
    
    # Filter out stop words
    words = [word for word in words if word not in stop_words]

    # Count frequencies
    word_counts = Counter(words)
    
    # Display results
    click.echo(f"\nTop {top} words in {text_file}:")
    click.echo("-" * 30)
    
    for word, count in word_counts.most_common(top):
        click.echo(f"{word:15} {count:5}")

if __name__ == '__main__':
    main()
