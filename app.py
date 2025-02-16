#/// script
# requires-python = ">=3.13"
# dependencies = [
#   "fastapi",
#   "uvicorn[standard]",
#   "requests",
# ]
#///

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import json
import subprocess
from typing import Dict, Any
import pandas as pd
import re
from dateutil import parser
from datetime import datetime
from pathlib import Path
import sqlite3
import openai
import itertools
import numpy as np
#from sentence_transformers import SentenceTransformer, util
#import torch

#api_key = os.environ.get("OPENAI_API_KEY")

api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AIPROXY_TOKEN")
if not api_key:
    raise ValueError("api_key is not set!")


#print("OPENAI_API_KEY:", api_key)
#if not api_key:
    #raise ValueError("api_key is not set!")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# A3
input_file = '/data/dates.txt'
output_file = '/data/dates-wednesdays.txt'
def count_wednesdays(input_file: str, output_file: str):
    """
    Reads a file containing dates, counts how many are Wednesdays, 
    and writes the count to an output file.
    
    :param input_file: Path to the input file containing dates.
    :param output_file: Path to the output file where the count will be saved.
    """
    wednesday_count = 0

    try:
        with open(input_file, 'r') as file:
            for line in file:
                line = line.strip()
                try:
                    parsed_date = parser.parse(line)
                    if parsed_date.weekday() == 2:  # Wednesday
                        wednesday_count += 1
                except (ValueError, TypeError):
                    print(f"Skipping invalid date: {line}")

        with open(output_file, 'w') as output:
            output.write(str(wednesday_count))

        print(f"Total Wednesdays counted: {wednesday_count}")

    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")

COUNT_WEDNESDAYS = {
    "type": "function",
    "function": {
        "name": "count_wednesdays",
        "description": "Counts the number of Wednesdays in a file containing dates and writes the result to an output file.",
        "parameters": {
            "type": "object",
            "properties": {
                "input_file": {
                    "type": "string",
                    "description": "Path to the input file containing dates, one per line."
                },
                "output_file": {
                    "type": "string",
                    "description": "Path to the output file where the Wednesday count will be stored."
                }
            },
            "required": ["input_file", "output_file"]
        }
    }
}
#A4
#input_location = '/data/contacts.json'
#output_location = '/data/contacts-sorted.json'
def sorted_contacts(input_location: str, output_location: str):
    # Check if file exists
    if not os.path.exists(input_location):
        return {"error": "Input file does not exist", "file": input_location}

    try:
        # Read and sort JSON
        contacts = pd.read_json(input_location)
        contacts.sort_values(["last_name", "first_name"], inplace=True)
        contacts.to_json(output_location, orient="records")

        return {"status": "Successfully created", "output_file": output_location}
    
    except ValueError as e:
        return {"error": "Invalid JSON format", "message": str(e)}


SORTED_CONTACTS = {
    "type": "function",  # ADD THIS LINE
    "function": {
        "name": "sorted_contacts",
        "description": "Sort a list of contacts by last name and first name",
        "parameters": {
            "type": "object",
            "properties": {
                "input_location": {
                    "type": "string",
                    "description": "The location of the input file"
                },
                "output_location": {
                    "type": "string",
                    "description": "The location of the output file"
                }
            },
            "required": ["input_location", "output_location"]
        }
    }
}



#A7
# Define file paths
input_file = '/data/email.txt'
output_file = '/data/email-sender.txt'

# Function to extract email address using regex
def extract_email(input_file: str, output_file: str):
    try:
        with open(input_file, 'r') as file:
            email_content = file.read()
        
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        matches = re.findall(email_pattern, email_content)
        
        if matches:
            sender_email = matches[0]
            with open(output_file, 'w') as output:
                output.write(sender_email)
            return {"message": f"Sender's email address extracted: {sender_email}"}
        else:
            return {"error": "No email address found in the content."}
    
    except Exception as e:
        return {"error": str(e)}

EXTRACT_EMAIL = {
    "type": "function",
    "function": {
        "name": "extract_email",
        "description": "Extracts the sender's email address from a given text file using regex.",
        "parameters": {
            "type": "object",
            "properties": {
                "input_file": {
                    "type": "string",
                    "description": "The path to the text file containing the email content."
                },
                "output_file": {
                    "type": "string",
                    "description": "The path where the extracted email address will be saved."
                }
            },
            "required": ["input_file", "output_file"]
        }
    }
}

#A5
def extract_recent_log_lines(logs_dir: str, output_file: str, max_files: int = 10):
    """
    Extracts the first line from the most recent log files and writes them to an output file.

    :param logs_dir: Path to the directory containing log files.
    :param output_file: Path to the output file where the extracted lines will be saved.
    :param max_files: Maximum number of recent log files to process (default is 10).
    """
    logs_path = Path(logs_dir)
    
    # Ensure the directory exists
    if not logs_path.exists() or not logs_path.is_dir():
        print(f"Error: Directory '{logs_dir}' does not exist or is not a directory.")
        return

    # Get all .log files in the directory and sort them by modification time (most recent first)
    log_files = sorted(logs_path.glob('*.log'), key=lambda x: x.stat().st_mtime, reverse=True)

    # Check if there are no log files
    if not log_files:
        print(f"Warning: No log files found in '{logs_dir}'.")
        return

    try:
        with open(output_file, 'w', encoding='utf-8') as output:
            for log_file in log_files[:max_files]:
                try:
                    with open(log_file, 'r', encoding='utf-8') as file:
                        first_line = file.readline().strip()
                        output.write(first_line + '\n')
                except Exception as e:
                    print(f"Error processing file {log_file}: {type(e).__name__}: {e}")

        print(f"The first lines of the {min(len(log_files), max_files)} most recent .log files have been written to {output_file}.")
    except Exception as e:
        print(f"Error writing output file '{output_file}': {type(e).__name__}: {e}")

EXTRACT_RECENT_LOG_LINES = {
  "type": "function",
  "function": {
    "name": "extract_recent_log_lines",
    "description": "Extracts the first line from the most recent log files and writes them to an output file.",
    "parameters": {
      "type": "object",
      "properties": {
        "logs_dir": {
          "type": "string",
          "description": "Path to the directory containing log files."
        },
        "output_file": {
          "type": "string",
          "description": "Path to the output file where the extracted lines will be saved."
        },
        "max_files": {
          "type": "integer",
          "description": "Maximum number of recent log files to process, default is 10.",
          "default": 10
        }
      },
      "required": ["logs_dir", "output_file"]
    }
  }
}

#A6
#docs_dir = '/data/docs/'
#output_file = '/data/docs/index.json'

def index_markdown_files(docs_dir: str, output_file: str):
    """
    Finds all Markdown (.md) files in the specified directory, extracts the first H1 title from each,
    and creates an index file mapping filenames to titles.

    :param docs_dir: Path to the directory containing Markdown files.
    :param output_file: Path to the JSON file where the index will be saved.
    """
    # Ensure docs_dir exists
    docs_path = Path(docs_dir)
    if not docs_path.exists() or not docs_path.is_dir():
        print(f"Error: Directory '{docs_dir}' does not exist or is not a directory.")
        return

    md_files = list(docs_path.glob('**/*.md'))  # Convert to list to check empty case
    if not md_files:
        print(f"Warning: No Markdown files found in '{docs_dir}'.")
    
    index = {}

    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as file:
                for line in file:
                    if line.startswith('# '):  # Find the first H1 title
                        title = line.lstrip('#').strip()
                        filename = str(md_file.relative_to(docs_dir))  # Get relative file path
                        index[filename] = title
                        break
        except Exception as e:
            print(f"Error processing file {md_file}: {type(e).__name__}: {e}")

    try:
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump(index, json_file, indent=4, ensure_ascii=False)

        print(f"Index file created: {output_file}")
    except Exception as e:
        print(f"Error writing index file '{output_file}': {type(e).__name__}: {e}")

# Function Calling Schema for GPT API
INDEX_MARKDOWN_FILES = {
    "type": "function",
    "function": {
        "name": "index_markdown_files",
        "description": "Finds all Markdown (.md) files in a specified directory, extracts the first H1 title from each, and creates an index file mapping filenames to titles.",
        "parameters": {
            "type": "object",
            "properties": {
                "docs_dir": {
                    "type": "string",
                    "description": "Path to the directory containing Markdown files."
                },
                "output_file": {
                    "type": "string",
                    "description": "Path to the JSON file where the index will be saved."
                }
            },
            "required": ["docs_dir", "output_file"]
        }
    }
}


#A10
def compute_gold_ticket_sales(db_path: str, output_file: str):
    """
    Computes the total sales for "Gold" tickets from an SQLite database and writes the result to a file.

    :param db_path: Path to the SQLite database file.
    :param output_file: Path to the output file where the total sales will be saved.
    """
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute the query to compute total sales for "Gold" tickets
        query = "SELECT SUM(units * price) FROM tickets WHERE type = 'Gold';"
        cursor.execute(query)
        result = cursor.fetchone()

        # If result is None or SUM returns NULL, set total_sales to 0
        total_sales = result[0] if result and result[0] is not None else 0

        # Close the database connection
        conn.close()

        # Write the result to the output file
        with open(output_file, 'w') as f:
            f.write(str(total_sales))

        print(f"Total sales for Gold ticket type ({total_sales}) written to {output_file}.")
    
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

COMPUTE_GOLD_TICKET_SALES = {
    "type": "function",
    "function": {
        "name": "compute_gold_ticket_sales",
        "description": "Computes the total sales for 'Gold' tickets from an SQLite database and writes the result to a file.",
        "parameters": {
            "type": "object",
            "properties": {
                "db_path": {
                    "type": "string",
                    "description": "Path to the SQLite database file."
                },
                "output_file": {
                    "type": "string",
                    "description": "Path to the output file where the total sales will be saved."
                }
            },
            "required": ["db_path", "output_file"]
        }
    }
}

tools = [
    {
        "type":"function",
        "function":{
            "name": "script_runner",
            "description": "Install a package and run a script from a url with provided arguments",
            "parameters": {
                "type": "object",
                "properties": {
                    "script_url": {
                        "type": "string",
                        "description": "The URL of the script to run"
                    },
                    "args": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of aruguments to pass to the script"
                    },
                },
                "required": ["package_name", "script_url", "args"]
            }
        }
    }
]


tools = [SORTED_CONTACTS, EXTRACT_EMAIL, COUNT_WEDNESDAYS, INDEX_MARKDOWN_FILES, 
EXTRACT_RECENT_LOG_LINES, COMPUTE_GOLD_TICKET_SALES]


@app.get("/")
def home():
    return {"message": "Yah TDS Wednesday is awesome"}

@app.get("/read")
def read_file(path: str):
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        raise HTTPException(status_code=404, detail="File doen't exist")
    

def query_gpt(user_input: str, tools: list[Dict[str, Any]] = tools) -> Dict[str, Any]:
    response = requests.post(
        url="https://aiproxy.sanand.workers.dev/openai/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": """whenever you receive a system directory location, always make it
                into a relative path, for example adding a . before it would make it relative path, rest is on
                you to manage, i just want the relative path."""},
                {"role": "user", "content": user_input}    
            ],
            "tools": tools,
            "tool_choice": "auto",
        },
    )

    result = response.json()

    # Handle API errors
    if 'error' in result:
        raise HTTPException(status_code=400, detail=f"OpenAI API Error: {result['error']['message']}")

    if 'choices' not in result:
        raise HTTPException(status_code=400, detail="Invalid response from OpenAI API: Missing 'choices'.")

    return result

def script_runner(script_url: str, args: list):
    command = ["uv", "run", script_url] + args
    result = subprocess.run(command, capture_output=True, text=True)
    return {"output": result.stdout, "error": result.stderr}


@app.get("/run")
async def run(task: str):
    query = query_gpt(task)
    print(query)
    func = eval(query['choices'][0]['message']['tool_calls'][0]['function']['name'])
    args = json.loads(query['choices'][0]['message']['tool_calls'][0]['function']['arguments'])
    output = func(**args)
    return output
    
    choices = response.json().get('choices')
    if choices:
        # Proceed with processing 'choices'
        first_choice = choices[0]
    else:
        print("Warning: 'choices' key is missing in the response.")
    
    script_url = arguments['script_url']
    email = arguments['args'][0]
    command = ["uv","run",script_url, email]
    subprocess.run(command)
    print("API Response:", response.json())

    if response.status_code != 200:
        print(f"Error: Received status code {response.status_code}")
        print("Response Content:", response.content)
        return

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)