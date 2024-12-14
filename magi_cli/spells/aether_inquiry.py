import click
import re
import os
import sys
from datetime import datetime
from pathlib import Path
from magi_cli.spells import SANCTUM_PATH
from openai import OpenAI

__requires__ = ['click', 'openai']

def is_readable(file_path):
    """Check if a file is readable as text."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            file.read(1024)  # Read only the first 1024 bytes for efficiency
            return True
    except (UnicodeDecodeError, IOError):
        return False

def read_directory(path, prefix="", md_file_name="directory_contents"):
    """Recursively read the contents of a directory and write them to a Markdown file in the .aether directory."""
    aether_dir = os.path.join(SANCTUM_PATH, '.aether')
    if not os.path.exists(aether_dir):
        os.makedirs(aether_dir)

    # Generate a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_file_name_with_timestamp = f"{md_file_name}_{timestamp}.md"
    markdown_file_path = os.path.join(aether_dir, md_file_name_with_timestamp)

    contents = ""
    with open(markdown_file_path, 'a', encoding='utf-8', errors='replace') as md_file:
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                dir_line = f"{prefix}/{item}/\n"
                contents += dir_line
                md_file.write(f"## {dir_line}\n")
                contents += read_directory(full_path, prefix=prefix + "/" + item, md_file_name=md_file_name)
            else:
                file_line = f"{prefix}/{item}: "
                if is_readable(full_path):
                    with open(full_path, 'r', encoding='utf-8', errors='replace') as file:
                        file_content = file.read()
                    file_line += f"\n```\n{file_content}\n```\n"
                else:
                    file_line += "[non-readable or binary content]\n"
                contents += file_line
                md_file.write(file_line)
    return contents

def get_enhanced_prompt():
    """Return enhanced system prompt with YAML spell creation knowledge."""
    return '''You are a technowizard trained in the arcane, specializing in spell creation through YAML configurations. 
You have deep knowledge of software development and computer science. You generate python scripts, bash scripts and spells in YAML. When creating spells, follow these guidelines:

1. Choose names for spells that reflect their purpose, for example:
   - echo (for a script that prints text)
   - mystic_portal (for a file transfer tool)
   - sacred_sentinel (for a monitoring script)
   - loci_logger (for a logging utility)
   - crystal_cipher (for an encryption tool)
   Always use underscores between words and keep names lowercase.

2. Generate complete YAML configurations following this structure:
   - name: Spell identifier (magical and evocative, lowercase with underscores)
   - description: Clear purpose description with a magical flavor
   - type: Usually 'bundled' or 'script'
   - shell_type: 'python' or 'bash'
   - requires: List of Python package dependencies
   - code: The main spell implementation (must include proper Click CLI setup)
   - artifacts: Any additional files needed

3. After providing the YAML configuration, always include this note, and format it with the generated spell name:
   "To create this spell, save the YAML to a file (e.g., <spell_name>.yaml) by entering `scribe` in the chat and then run:
   `cast sc <spell_name>.yaml` to create the spell in your .tome directory. You may then cast it at any time using `cast <spell_name>`."

Here is an example spell configuration:

```yaml
name: arcane_art
description: A spell to transmute plain text into mesmerizing ASCII art, using a selection of mystical fonts.
type: script
shell_type: python
requires:
  - art>=6.0
code: |
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
```

When generating python or bash scripts, use the following structure:

```bash
#!/usr/bin/env bash
# <description>
<content of script>
```

```python
# <description>
<content of script>
```

When providing a script, always include this note:
"To create this script, save the file to a text file (e.g., <script_name>.py or <script_name>.sh) by entering `scribe` in the chat. This will prompt you to save the file and you will select the file type.
It will then prompt for a name, and it will save the script in your current directory. You may then execute it."

Your responses for general queries should be informative and helpful, using your arcane knowledge
to assist with software development, system administration, and other technical tasks.'''

def send_message(message_log):
    """Send a message to the OpenAI API and return the response."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "OpenAI API key is not set. Unable to consult the aether for wisdom."
    
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4-0125-preview",  # Most recent model
            messages=message_log,
            max_tokens=4096,
            temperature=0.7,
        )
        return response.choices[0].message.content if response.choices else "No response received from the aether."
    except Exception as e:
        return f"Error consulting the aether: {str(e)}"

@click.command()
@click.argument('args', nargs=-1)
def aether_inquiry(args):
    """'ai' - Call upon an aether intelligence (OpenAI) to answer questions, generate spells, or converse about files and folders."""
    
    # Initialize message log with enhanced system prompt
    message_log = [
        {"role": "system", "content": get_enhanced_prompt()}
    ]

    # Check for previous conversations
    aether_dir = os.path.join(SANCTUM_PATH, '.aether')
    os.makedirs(aether_dir, exist_ok=True)
    
    previous_inquiries = [f for f in os.listdir(aether_dir) 
                         if f.startswith('Inquiry-') and f.endswith('.md')]

    if previous_inquiries:
        if click.confirm("Would you like to continue a previous conversation?"):
            print("\nSelect a previous conversation:")
            for idx, filename in enumerate(previous_inquiries, 1):
                print(f"{idx}. {filename}")
            
            selected = click.prompt("Enter conversation number (or press Enter to skip)", 
                                  type=click.INT, default=0, show_default=False)
            
            if 1 <= selected <= len(previous_inquiries):
                with open(os.path.join(aether_dir, previous_inquiries[selected-1]), 'r') as f:
                    message_log.append({"role": "user", "content": f.read()})
                print("\nPrevious conversation loaded. You may continue your inquiry.")

    # Handle file and directory inputs
    if args:
        for file_path in args:
            if os.path.isdir(file_path):
                if click.confirm(f"Transcribe contents of '{file_path}' directory?"):
                    directory_contents = read_directory(file_path)
                    message_log.append({"role": "user", "content": directory_contents})
            else:
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        message_log.append({"role": "user", "content": file.read()})
                except UnicodeDecodeError:
                    print(f"Unable to read '{file_path}' - file appears to be binary.")
        print("\nProvided files/folders have been analyzed. You may now inquire about them.")
    else:
        print("\nYou may begin your inquiry with the aether.")

    last_response = ""
    while True:
        user_input = click.prompt("You", type=str)

        if user_input.lower() == "quit":
            if click.confirm("Save this conversation?"):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                inquiry_filename = f"Inquiry-{timestamp}.md"
                
                with open(os.path.join(aether_dir, inquiry_filename), 'w') as f:
                    f.write(f"# Aether Inquiry Conversation - {timestamp}\n\n")
                    for message in message_log:
                        sender = 'User' if message['role'] == 'user' else 'mAGI'
                        f.write(f"{sender}: {message['content']}\n\n")
                print(f"Conversation saved as {inquiry_filename}")
            print("May your future inquiries be fruitful. Farewell.")
            break

        elif user_input.lower() == "scribe":
            save_format = click.prompt(
                "Save as",
                type=click.Choice(['yaml', 'python', 'bash', 'markdown', 'copy'], case_sensitive=False)
            )

            if save_format == "yaml":
                # Extract YAML content from code blocks
                yaml_blocks = re.findall(r'```yaml(.*?)```', last_response, re.DOTALL)
                if not yaml_blocks:
                    print("No YAML configuration found in the response.")
                    continue
                    
                yaml_content = yaml_blocks[0].strip()
                yaml_file_name = click.prompt("Enter name for YAML file (without extension)")
                
                with open(f"{yaml_file_name}.yaml", 'w') as f:
                    f.write(yaml_content)
                print(f"\nYAML configuration saved as {yaml_file_name}.yaml")
                print(f"\nTo create the spell, run:")
                print(f"cast sc {yaml_file_name}.yaml")

            elif save_format == "python":
                # Extract Python code blocks
                code_blocks = re.findall(r'```python(.*?)```', last_response, re.DOTALL)
                if not code_blocks:
                    # Try alternative code block format
                    code_blocks = re.findall(r'```py(.*?)```', last_response, re.DOTALL)
                
                if not code_blocks:
                    print("No Python code found in the response.")
                    continue
                
                # Combine all Python code blocks
                code = '\n\n'.join(block.strip() for block in code_blocks)
                python_file_name = click.prompt("Enter name for Python script (without extension)")
                
                with open(f"{python_file_name}.py", 'w') as f:
                    f.write(code)
                # Make executable
                Path(f"{python_file_name}.py").chmod(0o755)
                print(f"Python script saved as {python_file_name}.py")

            elif save_format == "bash":
                # Extract bash code blocks
                code_blocks = re.findall(r'```bash(.*?)```', last_response, re.DOTALL)
                if not code_blocks:
                    # Try alternative code block format
                    code_blocks = re.findall(r'```sh(.*?)```', last_response, re.DOTALL)
                
                if not code_blocks:
                    print("No bash code found in the response.")
                    continue
                
                # Combine all bash code blocks
                code = '\n\n'.join(block.strip() for block in code_blocks)
                bash_file_name = click.prompt("Enter name for bash script (without extension)")
                
                with open(f"{bash_file_name}.sh", 'w') as f:
                    f.write('#!/bin/bash\n\n' + code)
                # Make executable
                Path(f"{bash_file_name}.sh").chmod(0o755)
                print(f"Bash script saved as {bash_file_name}.sh")

            elif save_format == "markdown":
                md_file_name = click.prompt("Enter name for Markdown file (without extension)")
                with open(f"{md_file_name}.md", 'w') as md_file:
                    md_file.write(f"# Response\n\n{last_response}")
                print(f"Markdown saved as {md_file_name}.md")

            elif save_format == "copy":
                file_name = click.prompt("Enter name for text file (without extension)")
                with open(f"{file_name}.txt", 'w') as f:
                    f.write(last_response)
                print(f"Response saved as {file_name}.txt")

        else:
            message_log.append({"role": "user", "content": user_input})
            print("\nConsulting the aether...")
            response = send_message(message_log)
            message_log.append({"role": "assistant", "content": response})
            print(f"\nmAGI: {response}")
            last_response = response

alias = "ai"

def main():
    aether_inquiry()

if __name__ == '__main__':
    main()