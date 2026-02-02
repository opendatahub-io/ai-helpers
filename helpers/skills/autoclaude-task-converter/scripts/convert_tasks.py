#!/usr/bin/env python3
"""
Convert TASKS.md format to AutoClaude spec structure.

Usage:
    python convert_tasks.py --input TASKS.md --output .auto-claude/specs
    python convert_tasks.py --init --output .auto-claude/specs
"""

import argparse
import json
import re
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# Mapping tables
STATUS_MAP = {
    'to do': 'pending',
    'todo': 'pending',
    'in progress': 'in_progress',
    'in-progress': 'in_progress',
    'done': 'completed',
    'completed': 'completed',
    'blocked': 'blocked',
}

PRIORITY_MAP = {
    'critical': 'p0',
    'high': 'p1',
    'medium': 'p2',
    'low': 'p3',
}


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text[:50].rstrip('-')


def parse_task_block(block: str) -> Optional[dict]:
    """Parse a structured task block (### TASK-XXX format)."""
    lines = block.strip().split('\n')
    if not lines:
        return None
    
    # Extract task ID and title from header
    header_match = re.match(r'^###?\s*(?:TASK-)?(\d+):?\s*(.+)$', lines[0], re.IGNORECASE)
    if not header_match:
        return None
    
    task_id = header_match.group(1).zfill(3)
    title = header_match.group(2).strip()
    
    task = {
        'task_id': task_id,
        'title': title,
        'description': '',
        'area': 'General',
        'status': 'pending',
        'priority': 'p2',
        'dependencies': [],
        'subtasks': [],
        'notes': '',
        'completed_at': None,
    }
    
    current_field = None
    subtask_section = False
    
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        
        # Check for field markers
        field_match = re.match(r'^-\s*\*\*(\w+)\*\*:\s*(.*)$', line, re.IGNORECASE)
        if field_match:
            field_name = field_match.group(1).lower()
            field_value = field_match.group(2).strip()
            subtask_section = False
            
            if field_name == 'description':
                task['description'] = field_value
                current_field = 'description'
            elif field_name == 'area':
                task['area'] = field_value
            elif field_name == 'status':
                task['status'] = STATUS_MAP.get(field_value.lower(), 'pending')
            elif field_name == 'priority':
                task['priority'] = PRIORITY_MAP.get(field_value.lower(), 'p2')
            elif field_name in ('dependencies', 'depends'):
                deps = re.findall(r'TASK-?(\d+)', field_value, re.IGNORECASE)
                task['dependencies'] = [d.zfill(3) for d in deps]
            elif field_name == 'completed':
                task['completed_at'] = field_value
            elif field_name == 'notes':
                task['notes'] = field_value
                current_field = 'notes'
            elif field_name in ('subtasks', 'subtask'):
                subtask_section = True
                current_field = 'subtasks'
            continue
        
        # Check for subtask items
        subtask_match = re.match(r'^-?\s*\[([ xX])\]\s*(.+)$', line)
        if subtask_match:
            completed = subtask_match.group(1).lower() == 'x'
            subtask_text = subtask_match.group(2).strip()
            task['subtasks'].append({
                'title': subtask_text,
                'completed': completed
            })
            continue
        
        # Continuation of notes (lines starting with ✅ or other markers)
        if current_field == 'notes' and line:
            task['notes'] += '\n' + line
    
    return task


def parse_simple_task(line: str, index: int) -> Optional[dict]:
    """Parse a simple single-line task (- [ ] format)."""
    match = re.match(r'^-?\s*\[([ xX])\]\s*(.+)$', line.strip())
    if not match:
        return None
    
    completed = match.group(1).lower() == 'x'
    title = match.group(2).strip()
    
    return {
        'task_id': str(index).zfill(3),
        'title': title,
        'description': title,
        'area': 'General',
        'status': 'completed' if completed else 'pending',
        'priority': 'p2',
        'dependencies': [],
        'subtasks': [],
        'notes': '',
        'completed_at': None,
    }


def parse_tasks_file(filepath: Path) -> list[dict]:
    """Parse a TASKS.md file and extract all tasks."""
    content = filepath.read_text(encoding='utf-8')
    tasks = []
    
    # Split by task headers (### TASK-XXX)
    task_pattern = r'(###?\s*(?:TASK-?)?\d+:?.+?)(?=###?\s*(?:TASK-?)?\d+:|$)'
    blocks = re.findall(task_pattern, content, re.DOTALL | re.IGNORECASE)
    
    for block in blocks:
        task = parse_task_block(block)
        if task:
            tasks.append(task)
    
    # Also look for simple checkbox tasks not in blocks
    simple_task_index = len(tasks) + 1
    for line in content.split('\n'):
        if re.match(r'^-?\s*\[[ xX]\]\s+\w', line):
            # Check if this line is already part of a structured task
            is_subtask = False
            for task in tasks:
                if any(st['title'] in line for st in task['subtasks']):
                    is_subtask = True
                    break
            
            if not is_subtask:
                simple_task = parse_simple_task(line, simple_task_index)
                if simple_task:
                    tasks.append(simple_task)
                    simple_task_index += 1
    
    return tasks


def assess_complexity(task: dict) -> str:
    """Determine task complexity based on subtasks and description."""
    subtask_count = len(task['subtasks'])
    desc_length = len(task.get('description', ''))
    dep_count = len(task.get('dependencies', []))
    
    if subtask_count >= 7 or dep_count >= 3:
        return 'complex'
    elif subtask_count >= 3 or desc_length > 200:
        return 'standard'
    return 'simple'


def create_spec_md(task: dict) -> str:
    """Generate spec.md content."""
    lines = [
        f"# {task['title']}",
        "",
        "## Overview",
        task['description'] or "TODO: Add description",
        "",
        "## Requirements",
    ]
    
    if task['subtasks']:
        for st in task['subtasks']:
            lines.append(f"- {st['title']}")
    else:
        lines.append("- TODO: Define requirements")
    
    lines.extend([
        "",
        "## Acceptance Criteria",
    ])
    
    if task['subtasks']:
        for st in task['subtasks']:
            checkbox = "[x]" if st['completed'] else "[ ]"
            lines.append(f"- {checkbox} {st['title']}")
    else:
        lines.append("- [ ] TODO: Define acceptance criteria")
    
    lines.extend([
        "",
        "## Technical Approach",
        "TODO: Define implementation approach",
        "",
    ])
    
    if task['dependencies']:
        lines.append("## Dependencies")
        for dep in task['dependencies']:
            lines.append(f"- TASK-{dep}")
        lines.append("")
    
    if task['notes']:
        lines.extend([
            "## Notes",
            task['notes'],
            "",
        ])
    
    return '\n'.join(lines)


def create_requirements_json(task: dict) -> dict:
    """Generate requirements.json content."""
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    return {
        "task_id": task['task_id'],
        "task_name": slugify(task['title']),
        "title": task['title'],
        "description": task['description'],
        "area": task['area'],
        "status": task['status'],
        "priority": task['priority'],
        "complexity": assess_complexity(task),
        "dependencies": task['dependencies'],
        "acceptance_criteria": [st['title'] for st in task['subtasks']] or ["TODO: Define criteria"],
        "notes": task['notes'],
        "created_at": now,
        "updated_at": now,
        "completed_at": task['completed_at'],
    }


def create_context_json() -> dict:
    """Generate empty context.json template."""
    return {
        "project_type": None,
        "relevant_files": [],
        "dependencies": {
            "runtime": [],
            "dev": []
        },
        "patterns_discovered": [],
        "related_specs": []
    }


def create_implementation_plan(task: dict) -> dict:
    """Generate implementation_plan.json content."""
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    complexity = assess_complexity(task)
    
    chunks = []
    for i, subtask in enumerate(task['subtasks'], 1):
        chunks.append({
            "id": i,
            "title": subtask['title'],
            "description": subtask['title'],
            "status": "completed" if subtask['completed'] else "pending",
            "files_to_modify": [],
            "files_to_create": [],
            "acceptance_criteria": [subtask['title']],
            "dependencies": [i - 1] if i > 1 else [],
            "session_count": 0,
            "last_session": None
        })
    
    # If no subtasks, create a single chunk
    if not chunks:
        chunks.append({
            "id": 1,
            "title": task['title'],
            "description": task['description'] or task['title'],
            "status": "completed" if task['status'] == 'completed' else "pending",
            "files_to_modify": [],
            "files_to_create": [],
            "acceptance_criteria": ["TODO: Define criteria"],
            "dependencies": [],
            "session_count": 0,
            "last_session": None
        })
    
    completed = sum(1 for c in chunks if c['status'] == 'completed')
    
    return {
        "spec_id": task['task_id'],
        "spec_name": slugify(task['title']),
        "complexity": complexity,
        "total_chunks": len(chunks),
        "completed_chunks": completed,
        "status": task['status'],
        "chunks": chunks,
        "created_at": now,
        "updated_at": now
    }


def create_spec_directory(task: dict, output_dir: Path) -> Path:
    """Create the spec directory with all files."""
    spec_name = f"{task['task_id']}-{slugify(task['title'])}"
    spec_dir = output_dir / spec_name
    spec_dir.mkdir(parents=True, exist_ok=True)
    
    # Write spec.md
    (spec_dir / 'spec.md').write_text(create_spec_md(task), encoding='utf-8')
    
    # Write requirements.json
    (spec_dir / 'requirements.json').write_text(
        json.dumps(create_requirements_json(task), indent=2),
        encoding='utf-8'
    )
    
    # Write context.json
    (spec_dir / 'context.json').write_text(
        json.dumps(create_context_json(), indent=2),
        encoding='utf-8'
    )
    
    # Write implementation_plan.json
    (spec_dir / 'implementation_plan.json').write_text(
        json.dumps(create_implementation_plan(task), indent=2),
        encoding='utf-8'
    )
    
    return spec_dir


def init_project(output_dir: Path) -> None:
    """Initialize a new project with AutoClaude structure."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create template TASKS.md
    tasks_template = """# TASKS.md

## Development Backlog

### Legend
- 📋 **Status**: `To Do` | `In Progress` | `Done` | `Blocked`
- 🎯 **Priority**: `Critical` | `High` | `Medium` | `Low`
- 🏷️ **Area**: Component/Feature area
- 📝 **Notes**: Additional context, blockers, dependencies

---

## Foundation Tasks

### TASK-001: Project Setup
- **Description**: Initialize project structure and dependencies
- **Area**: Infrastructure
- **Status**: To Do
- **Priority**: Critical
- **Subtasks**:
  - [ ] Initialize repository
  - [ ] Set up development environment
  - [ ] Configure linting and formatting
  - [ ] Create initial documentation

---

## Feature Tasks

### TASK-002: Example Feature
- **Description**: Implement example feature
- **Area**: Features
- **Status**: To Do
- **Priority**: High
- **Dependencies**: TASK-001
- **Subtasks**:
  - [ ] Design component structure
  - [ ] Implement core logic
  - [ ] Add tests
  - [ ] Update documentation
"""
    
    parent_dir = output_dir.parent
    tasks_file = parent_dir / 'TASKS.md'
    tasks_file.write_text(tasks_template, encoding='utf-8')
    
    # Create sample spec
    sample_task = {
        'task_id': '001',
        'title': 'Project Setup',
        'description': 'Initialize project structure and dependencies',
        'area': 'Infrastructure',
        'status': 'pending',
        'priority': 'p0',
        'dependencies': [],
        'subtasks': [
            {'title': 'Initialize repository', 'completed': False},
            {'title': 'Set up development environment', 'completed': False},
            {'title': 'Configure linting and formatting', 'completed': False},
            {'title': 'Create initial documentation', 'completed': False},
        ],
        'notes': '',
        'completed_at': None,
    }
    
    create_spec_directory(sample_task, output_dir)
    
    print(f"✅ Initialized AutoClaude structure:")
    print(f"   📄 {tasks_file}")
    print(f"   📁 {output_dir}/001-project-setup/")


def main():
    parser = argparse.ArgumentParser(
        description='Convert TASKS.md to AutoClaude spec structure'
    )
    parser.add_argument(
        '--input', '-i',
        type=Path,
        help='Input TASKS.md file'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('.auto-claude/specs'),
        help='Output directory for specs (default: .auto-claude/specs)'
    )
    parser.add_argument(
        '--init',
        action='store_true',
        help='Initialize new project with AutoClaude structure'
    )
    parser.add_argument(
        '--filter-status',
        choices=['pending', 'in_progress', 'completed', 'blocked'],
        help='Only convert tasks with this status'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be created without creating files'
    )
    
    args = parser.parse_args()
    
    if args.init:
        init_project(args.output)
        return
    
    if not args.input:
        parser.error("--input is required unless using --init")
    
    if not args.input.exists():
        print(f"❌ Input file not found: {args.input}")
        return 1
    
    tasks = parse_tasks_file(args.input)
    
    if args.filter_status:
        tasks = [t for t in tasks if t['status'] == args.filter_status]
    
    if not tasks:
        print("⚠️  No tasks found in input file")
        return 0
    
    print(f"📋 Found {len(tasks)} task(s)")
    
    for task in tasks:
        if args.dry_run:
            spec_name = f"{task['task_id']}-{slugify(task['title'])}"
            print(f"   Would create: {args.output}/{spec_name}/")
        else:
            spec_dir = create_spec_directory(task, args.output)
            print(f"   ✅ Created: {spec_dir}")
    
    if not args.dry_run:
        print(f"\n✅ Converted {len(tasks)} task(s) to {args.output}")


if __name__ == '__main__':
    exit(main() or 0)
