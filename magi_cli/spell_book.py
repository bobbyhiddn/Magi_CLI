import inspect
import spells

def create_spell_book():
    '''This function creates a spell book from the spells.py file by reading each function and creating a file in the .orb directorry with the function's code under a .spell file for each function.'''
    spell_book = {}
    for name, obj in inspect.getmembers(spells):
        if inspect.isfunction(obj):
            spell_book[name] = inspect.getdoc(obj)
    return spell_book

