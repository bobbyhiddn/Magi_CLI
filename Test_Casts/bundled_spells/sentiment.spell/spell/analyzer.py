#!/usr/bin/env python3
import click
from textblob import TextBlob
from pathlib import Path
import json

def get_emoji(polarity):
    if polarity > 0.5:
        return "😄"
    elif polarity > 0:
        return "🙂"
    elif polarity == 0:
        return "😐"
    elif polarity > -0.5:
        return "🙁"
    else:
        return "😢"

@click.command()
@click.argument('text_file', type=click.Path(exists=True), required=False)
def main(text_file):
    """Analyze the sentiment of text using TextBlob."""
    
    # Get spell directory
    spell_dir = Path(__file__).parent.parent
    
    # Use sample.txt if no file specified
    if text_file is None:
        text_file = str(spell_dir / 'artifacts' / 'samples' / 'positive.txt')
        click.echo("No input file specified. Using positive sample...")
    
    # Read and analyze the text
    with open(text_file, 'r', encoding='utf-8') as f:
        text = f.read().strip()
    
    blob = TextBlob(text)
    
    # Get overall sentiment
    overall_sentiment = blob.sentiment
    
    click.echo("\n📝 Text Analysis Results")
    click.echo("=" * 50)
    click.echo(f"\n📊 Overall Sentiment: {get_emoji(overall_sentiment.polarity)}")
    click.echo(f"   Polarity: {overall_sentiment.polarity:.2f} (-1 negative to +1 positive)")
    click.echo(f"   Subjectivity: {overall_sentiment.subjectivity:.2f} (0 objective to 1 subjective)")
    
    # Analyze individual sentences
    click.echo("\n📈 Sentence-by-Sentence Analysis:")
    click.echo("-" * 50)
    
    for i, sentence in enumerate(blob.sentences, 1):
        emoji = get_emoji(sentence.sentiment.polarity)
        click.echo(f"\n{i}. {emoji} {sentence}")
        click.echo(f"   Polarity: {sentence.sentiment.polarity:.2f}")
        click.echo(f"   Subjectivity: {sentence.sentiment.subjectivity:.2f}")

if __name__ == '__main__':
    main()
