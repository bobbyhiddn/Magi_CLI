import click
import re
from openai import OpenAI

# Instantiate the OpenAI client
client = OpenAI()

def send_message(message_log):
    # Use the new chat completions API
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",  # Keep the model as is
        messages=message_log,
        max_tokens=1500,
        temperature=0.7,
    )

    # Adjusted response handling
    return response.choices[0].message.content if response.choices else ""


@click.command()
@click.argument('file_paths', nargs=-1)  # Accepts multiple file paths
def aether_inquiry(file_paths):
    """Call upon the arcane intellect of an artificial intelligence to answer your questions and generate spells or Python scripts."""

    message_log = [
        {"role": "system", "content": "You are a wizard trained in the arcane. You have deep knowledge of software development and computer science. You can cast spells and read tomes to gain knowledge about problems. Please greet the user. All code and commands should be in code blocks in order to properly help the user craft spells."}
    ]

    # Process each file path provided
    for file_path in file_paths:
        with open(file_path, 'r') as file:
            file_content = file.read()
        message_log.append({"role": "user", "content": file_content})

    last_response = ""
    first_request = False

    # Process each file path provided
    for file_path in file_paths:
        with open(file_path, 'r') as file:
            file_content = file.read()
        message_log.append({"role": "user", "content": file_content})

    while True:
        user_input = input("You: ")

        if user_input.lower() == "quit":
            print("I await your summons.")
            break

        elif user_input.lower() == "scribe":
            # Prompt the user whether they want to save the last response as a spell file, bash file, Python script, or just copy the last message
            save_prompt = input("Do you want to save the last response as a spell file, bash file, Python script, or just copy the last message? (spell/bash/python/copy/none): ")

            if save_prompt.lower() == "spell":
                # Save as spell file
                code_blocks = re.findall(r'(```bash|`)(.*?)(```|`)', last_response, re.DOTALL)
                code = '\n'.join(block[1].strip() for block in code_blocks)
                spell_file_name = input("Enter the name for the spell file (without the .spell extension): ")
                spell_file_path = f".tome/{spell_file_name}.spell"
                with open(spell_file_path, 'w') as f:
                    if code_blocks:
                        f.write(code)
                    else:
                        f.write(last_response)
                print(f"Spell saved as {spell_file_name}.spell in .tome directory.")

            elif save_prompt.lower() == "bash":
                # Save as bash file
                code_blocks = re.findall(r'(```bash|`)(.*?)(```|`)', last_response, re.DOTALL)
                code = '\n'.join(block[1].strip() for block in code_blocks)
                bash_file_name = input("Enter the name for the Bash script (without the .sh extension): ")
                with open(f"{bash_file_name}.sh", 'w') as f:
                    if code_blocks:
                        f.write(code)
                    else:
                        f.write(last_response)
                print(f"Bash script saved as {bash_file_name}.sh.")

            elif save_prompt.lower() == "python":
                # Save as Python script
                code_blocks = re.findall(r'(```python|`)(.*?)(```|`)', last_response, re.DOTALL)
                code = '\n'.join(block[1].strip() for block in code_blocks)
                python_file_name = input("Enter the name for the Python script (without the .py extension): ")
                with open(f"{python_file_name}.py", 'w') as f:
                    if code_blocks:
                        f.write(code)
                    else:
                        f.write(last_response)
                print(f"Python script saved as {python_file_name}.py.")

            elif save_prompt.lower() == "copy":
                # Copy the last message
                code = last_response
                message_file_name = input("Enter the name for the message file (without the .txt extension): ")
                with open(f"{message_file_name}.txt", 'w') as f:
                    f.write(code)
                print(f"Message saved as {message_file_name}.txt.")
        else:
            message_log.append({"role": "user", "content": user_input})
            print("Querying the aether...")
            response = send_message(message_log)
            message_log.append({"role": "assistant", "content": response})
            print(f"mAGI: {response}")
            last_response = response

if __name__ == '__main__':
    aether_inquiry()