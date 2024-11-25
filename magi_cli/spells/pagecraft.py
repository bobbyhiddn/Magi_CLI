import sys
import os
import re
import requests
from bs4 import BeautifulSoup
import click
from openai import OpenAI
from magi_cli.spells import SANCTUM_PATH

# Load the OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("Please set the OPENAI_API_KEY environment variable.")
    sys.exit(1)
else:
    client = OpenAI(api_key=api_key)

# Function to send a message to the OpenAI chatbot model and return its response
def send_message(message_log):
    if client:
        response = client.chat.completions.create(
            model="chatgpt-4o-latest",
            messages=message_log,
            max_tokens=12000,
            temperature=0.7,
        )
        return response.choices[0].message.content if response.choices else "No response received."
    else:
        return "OpenAI API key is not set. Unable to send message."

# Fetch the content from the given URL
def fetch_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

# Parse the fetched HTML content
def parse_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.string if soup.title else "Untitled"
    # Extract all text content from the HTML, including scripts and styles
    body = soup.get_text(separator='\n')
    return title, body

# Clean the content
def clean_content(content):
    # Preserve the content as much as possible
    content = content.replace('â', "'").replace('ð', '🎉')
    # Retain multiple newlines to preserve formatting
    content = re.sub(r'\r\n|\r', '\n', content).strip()
    return content

# Create the first draft of the Markdown content
def to_markdown(title, body):
    message_log = [
        {"role": "system", "content": (
            "You are an AI assistant that converts HTML content into a Markdown document. "
            "Please format the following content into Markdown, preserving all content exactly as it appears. "
            "Maintain the original structure, tone, and any repeated phrases or sections. "
            "Do not exclude any content. Thank you."
        )},
        {"role": "user", "content": f"# {title}\n\n{body}"}
    ]
    first_draft = send_message(message_log)
    return first_draft  # Return the first draft instead of saving it here

# Function to improve the Markdown content based on the review
def improve_markdown(first_draft, review_feedback, title, body):
    message_log = [
        {"role": "system", "content": (
            "You are an AI assistant that improves Markdown documents based on review feedback. "
            "Please revise the following Markdown content according to the feedback provided."
            "Only provide the markdown content; do not include any review feedback in the response."
            "Be as comprehensive as possible in addressing the feedback as well as improving the overall quality of the content."
            "Do not wrap the content in a markdown code block, just provide the content as markdown."
        )},
        {"role": "user", "content": (
            f"Markdown Content:\n{first_draft}\n\n"
            f"Review Feedback:\n{review_feedback}"
            f"Original Content:\n{title}\n{body}"
        )}
    ]
    improved_content = send_message(message_log)
    return improved_content

# Review the Markdown content using AI and get feedback
def review_content(original_content, markdown_content):
    review_message_log = [
        {"role": "system", "content": (
            "You are an AI assistant trained to review a transcribed Markdown document against the original content. "
            "Please provide detailed feedback on how well the content was transcribed, noting any discrepancies or issues. "
            "Do not provide a rating; instead, focus on actionable feedback that can help improve the transcription."
        )},
        {"role": "user", "content": (
            f"Original Content:\n{original_content}\n\n"
            f"Markdown Content:\n{markdown_content}"
        )}
    ]
    review_feedback = send_message(review_message_log)
    return review_feedback

# Perform a final review and display it to the CLI
def final_review(original_content, improved_content):
    final_review_message_log = [
        {"role": "system", "content": (
            "You are an AI assistant trained to perform a final review of the improved Markdown document against the original content. "
            "Please provide a detailed review of how well the content was transcribed and improved, noting any remaining discrepancies or issues. "
            "Rate the transcription quality on a scale from 1 to 10, where 10 means the content is perfectly transcribed, and 1 means it is poorly transcribed. "
            "Include the rating at the end of your review."
        )},
        {"role": "user", "content": (
            f"Original Content:\n{original_content}\n\n"
            f"Improved Markdown Content:\n{improved_content}"
        )}
    ]
    final_review = send_message(final_review_message_log)
    print(f"Final AI Review:\n{final_review}")

# Update the main function to include the new stages
@click.command()
@click.argument('args', nargs=-1)  # Accept multiple arguments like other spells
def pagecraft(args):
    """'pgc' - Craft a Markdown page from a URL through the use of aether inquiry(AI)."""

    if not args:
        print("Please provide a URL to craft a page from.")
        sys.exit(1)
    
    url = args[0]  # Take the first argument as the URL
    print("Fetching content.")
    html = fetch_content(url)
    title, body = parse_content(html)
    print(f"Title: {title}")
    body = clean_content(body)
    
    # Stage 1: Generate the first draft
    print("Generating the first draft.")
    first_draft = to_markdown(title, body)
    
    # Stage 2: Review the first draft
    print("Reviewing the first draft.")
    review_feedback = review_content(body, first_draft)
    
    # Stage 3: Improve the Markdown content based on the review
    print("Improving the Markdown content.")
    improved_content = improve_markdown(first_draft, review_feedback, title, body)
    
    # Generate a filename using the AI
    print("Generating a suitable filename.")
    filename_message_log = [
        {"role": "system", "content": "You are an AI trained to generate a suitable filename. Please generate a filename based on the following content."},
        {"role": "user", "content": improved_content}
    ]
    filename = send_message(filename_message_log)
    
    # Replace any characters that are not suitable for filenames
    filename = filename.replace(' ', '_').replace('/', '_').replace(':', '_').replace('"', '').replace('.txt', '').replace('`', '')
    
    # Ensure the filename does not have duplicate extensions
    if not filename.endswith(".md"):
        filename += ".md"
    
    # Check for SCRAPE_ARCHIVE_PATH environment variable
    archive_path = os.getenv('SCRAPE_ARCHIVE_PATH')

    if archive_path:
        print(f"The environment variable SCRAPE_ARCHIVE_PATH is set to: {archive_path}")
        save_in_archive = click.prompt("Do you want to save the file in the scrape archive path? (Y/n)", default='Y')
        if save_in_archive.lower() in ['y', 'yes', '']:
            save_dir = archive_path
        else:
            save_dir = os.getcwd()
    else:
        print("You can set the SCRAPE_ARCHIVE_PATH environment variable if you want the document to be generated in a specific location.")
        save_dir = os.getcwd()

    # Ensure the directory exists
    if not os.path.exists(save_dir):
        os.makedirs(save_dir, exist_ok=True)

    # Save the improved content to a file in the chosen directory
    full_path = os.path.join(save_dir, filename)
    with open(full_path, "w", encoding='utf-8') as f:
        f.write(improved_content)

    # Stage 4: Perform a final review and display it to the CLI
    final_review(body, improved_content)

    print(f"Content saved to {full_path}")

alias = "pgc"

def main():
    pagecraft()

# Entry point
if __name__ == "__main__":
    main()