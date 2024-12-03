#!/usr/bin/env python3
from art import text2art
import random
import sys

FONTS = ['block', 'banner', 'standard', 'avatar', 'basic', 'bigchief', 'cosmic', 'digital', 
         'dotmatrix', 'drpepper', 'epic', 'isometric1', 'letters', 'alligator', 'crazy', 'doom']

def main():
    # Get text from args or use default
    text = sys.argv[1] if len(sys.argv) > 1 else "Magic!"
    
    # Try with a random font first
    font = random.choice(FONTS)
    try:
        art = text2art(text, font=font)
        print(f"\nUsing font: {font}\n")
        print(art)
    except Exception as e:
        print(f"Error with font {font}: {e}")
        print("\nTrying with standard font instead...")
        print(text2art(text))

if __name__ == '__main__':
    main()
