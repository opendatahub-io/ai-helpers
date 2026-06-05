#!/usr/bin/env python3
"""
Create Google Doc from Markdown - Final Version
Fixed: Proper bullet nesting with polished formatting
"""

import os
import sys
import re
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/documents',
          'https://www.googleapis.com/auth/drive.file']

def get_credentials():
    """Get or refresh Google API credentials"""
    creds = None
    token_path = os.path.expanduser('~/.google-docs-token.pickle')
    creds_path = os.path.expanduser('~/.google-docs-credentials.json')

    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                print(f"ERROR: Credentials file not found at {creds_path}")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return creds

def clean_markdown_line(line):
    """Remove all markdown syntax from a line"""
    cleaned = line

    # Remove heading markers
    cleaned = re.sub(r'^#{1,6}\s+', '', cleaned)

    # Remove bullet markers but preserve indent
    if cleaned.lstrip().startswith('- ') or cleaned.lstrip().startswith('* '):
        leading_spaces = len(cleaned) - len(cleaned.lstrip())
        cleaned = ' ' * leading_spaces + cleaned.lstrip()[2:]

    # Convert markdown links to plain text: [text](url) -> text
    cleaned = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cleaned)

    # Remove bold markers
    cleaned = cleaned.replace('**', '')

    # Strip final whitespace
    cleaned = cleaned.strip()

    return cleaned

def parse_markdown_to_requests(markdown_content):
    """Parse markdown and create Google Docs API requests with polished formatting"""
    lines = markdown_content.split('\n')
    requests = []

    # Build full text with markdown removed
    full_text = ""
    text_map = []

    # Track empty lines to reduce excessive spacing
    consecutive_empty = 0

    for line in lines:
        start_idx = len(full_text) + 1

        # Reduce multiple consecutive blank lines to single blank line
        if not line.strip():
            consecutive_empty += 1
            if consecutive_empty > 1:
                continue
        else:
            consecutive_empty = 0

        # Clean the line
        display_line = clean_markdown_line(line)

        full_text += display_line + '\n'
        end_idx = len(full_text)

        text_map.append({
            'original': line,
            'display': display_line,
            'start': start_idx,
            'end': end_idx,
            'is_empty': not line.strip()
        })

    # Insert all text
    requests.append({
        'insertText': {
            'location': {'index': 1},
            'text': full_text
        }
    })

    # Collect all bullets to handle nesting properly
    bullet_items = []

    # Apply formatting
    for item in text_map:
        line = item['original']
        display = item['display']
        start = item['start']
        end = item['end'] - 1

        if item['is_empty']:
            continue

        # Headers with very tight spacing
        if line.startswith('# '):
            requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': start, 'endIndex': end},
                    'paragraphStyle': {
                        'namedStyleType': 'HEADING_1',
                        'spaceAbove': {'magnitude': 6, 'unit': 'PT'},
                        'spaceBelow': {'magnitude': 3, 'unit': 'PT'}
                    },
                    'fields': 'namedStyleType,spaceAbove,spaceBelow'
                }
            })
        elif line.startswith('## '):
            requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': start, 'endIndex': end},
                    'paragraphStyle': {
                        'namedStyleType': 'HEADING_2',
                        'spaceAbove': {'magnitude': 4, 'unit': 'PT'},
                        'spaceBelow': {'magnitude': 2, 'unit': 'PT'}
                    },
                    'fields': 'namedStyleType,spaceAbove,spaceBelow'
                }
            })
        elif line.startswith('### '):
            requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': start, 'endIndex': end},
                    'paragraphStyle': {
                        'namedStyleType': 'HEADING_3',
                        'spaceAbove': {'magnitude': 3, 'unit': 'PT'},
                        'spaceBelow': {'magnitude': 2, 'unit': 'PT'}
                    },
                    'fields': 'namedStyleType,spaceAbove,spaceBelow'
                }
            })

        # Bullets - collect them
        elif line.strip().startswith('- ') or line.strip().startswith('* '):
            stripped = line.lstrip()
            indent_count = len(line) - len(stripped)

            if indent_count >= 4:
                nesting_level = min(indent_count // 4, 8)
            elif indent_count >= 2:
                nesting_level = min(indent_count // 2, 8)
            else:
                nesting_level = 0

            bullet_items.append({
                'start': start,
                'end': end,
                'level': nesting_level
            })

        # Horizontal rules
        elif line.strip().startswith('---') or line.strip().startswith('━'):
            requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': start, 'endIndex': end},
                    'textStyle': {
                        'foregroundColor': {
                            'color': {
                                'rgbColor': {'red': 0.85, 'green': 0.85, 'blue': 0.85}
                            }
                        },
                        'fontSize': {'magnitude': 8, 'unit': 'PT'}
                    },
                    'fields': 'foregroundColor,fontSize'
                }
            })
            requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': start, 'endIndex': end},
                    'paragraphStyle': {
                        'spaceAbove': {'magnitude': 4, 'unit': 'PT'},
                        'spaceBelow': {'magnitude': 4, 'unit': 'PT'}
                    },
                    'fields': 'spaceAbove,spaceBelow'
                }
            })

        # Regular paragraphs
        elif not (line.startswith('#') or line.strip().startswith('-') or line.strip().startswith('*')):
            if line.strip():
                requests.append({
                    'updateParagraphStyle': {
                        'range': {'startIndex': start, 'endIndex': end},
                        'paragraphStyle': {
                            'spaceAbove': {'magnitude': 2, 'unit': 'PT'},
                            'spaceBelow': {'magnitude': 2, 'unit': 'PT'}
                        },
                        'fields': 'spaceAbove,spaceBelow'
                    }
                })

        # Bold text
        if '**' in line:
            parts = line.split('**')
            for i in range(len(parts)):
                if i % 2 == 1:
                    bold_text = parts[i]
                    cleaned_before = clean_markdown_line(''.join(parts[:i]))
                    bold_start = start + len(cleaned_before)
                    bold_end = bold_start + len(bold_text)

                    if bold_text.strip():
                        requests.append({
                            'updateTextStyle': {
                                'range': {'startIndex': bold_start, 'endIndex': bold_end},
                                'textStyle': {'bold': True},
                                'fields': 'bold'
                            }
                        })

        # Links
        if '[' in line and '](' in line:
            for match in re.finditer(r'\[([^\]]+)\]\(([^\)]+)\)', line):
                link_text = match.group(1)
                link_url = match.group(2)

                text_before = line[:match.start()]
                cleaned_before = clean_markdown_line(text_before)

                link_start = start + len(cleaned_before)
                link_end = link_start + len(link_text)

                requests.append({
                    'updateTextStyle': {
                        'range': {'startIndex': link_start, 'endIndex': link_end},
                        'textStyle': {
                            'link': {'url': link_url},
                            'foregroundColor': {
                                'color': {
                                    'rgbColor': {'red': 0.06, 'green': 0.33, 'blue': 0.8}
                                }
                            },
                            'underline': True
                        },
                        'fields': 'link,foregroundColor,underline'
                    }
                })

    # Now handle all bullets properly
    # First create bullets for all items
    if bullet_items:
        for bullet in bullet_items:
            requests.append({
                'createParagraphBullets': {
                    'range': {'startIndex': bullet['start'], 'endIndex': bullet['end']},
                    'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE'
                }
            })

        # Then apply nesting levels and spacing
        # Group consecutive bullets and track nesting
        for i, bullet in enumerate(bullet_items):
            # Set the nesting level using indentStart
            paragraph_style = {
                'spaceAbove': {'magnitude': 2, 'unit': 'PT'},
                'spaceBelow': {'magnitude': 2, 'unit': 'PT'},
                'lineSpacing': 110
            }

            # For nested bullets, calculate proper indent
            if bullet['level'] > 0:
                # Each level is 36pt (0.5 inch)
                indent_pt = bullet['level'] * 36
                paragraph_style['indentStart'] = {'magnitude': indent_pt, 'unit': 'PT'}
                # Also update the hanging indent for the bullet itself
                paragraph_style['indentFirstLine'] = {'magnitude': indent_pt, 'unit': 'PT'}

            fields = 'spaceAbove,spaceBelow,lineSpacing'
            if bullet['level'] > 0:
                fields += ',indentStart,indentFirstLine'

            requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': bullet['start'], 'endIndex': bullet['end']},
                    'paragraphStyle': paragraph_style,
                    'fields': fields
                }
            })

    return requests

def create_google_doc(title, markdown_file):
    """Create a Google Doc from markdown file"""

    print(f"Reading markdown from {markdown_file}...")
    with open(markdown_file, 'r') as f:
        markdown_content = f.read()

    print("Getting Google API credentials...")
    creds = get_credentials()

    print("Creating Google Doc...")
    try:
        docs_service = build('docs', 'v1', credentials=creds)

        # Create empty document
        doc = docs_service.documents().create(body={'title': title}).execute()
        doc_id = doc['documentId']

        print(f"Document created with ID: {doc_id}")

        # Generate formatting requests
        print("Converting markdown to Google Docs format...")
        requests = parse_markdown_to_requests(markdown_content)

        # Execute all requests in one batch
        print("Applying formatting...")
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()

        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

        print(f"\n✅ Success!")
        print(f"📄 Google Doc created: {doc_url}")
        print(f"\n💡 Professional formatting applied:")
        print(f"   ✓ Proper bullet nesting")
        print(f"   ✓ Tighter section spacing")
        print(f"   ✓ Clickable Jira links")
        print(f"   ✓ Clean layout")

        return doc_url

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python create-google-doc-final.py <markdown-file>")
        print("Example: python create-google-doc-final.py sprint-planning-2026-06-08.md")
        sys.exit(1)

    markdown_file = sys.argv[1]

    if not os.path.exists(markdown_file):
        print(f"ERROR: File not found: {markdown_file}")
        sys.exit(1)

    title = os.path.basename(markdown_file).replace('.md', '').replace('-', ' ').title()

    create_google_doc(title, markdown_file)

if __name__ == '__main__':
    main()
