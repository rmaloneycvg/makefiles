#!/usr/bin/env python3
"""
INOVAR code search utility.

Usage:
    search.py <search_term> [cs|js|sql|logs|docs|go|vb|py|java]

Type scopes:
  cs    .cs and .cshtml files
  js    .js, .jsx, .ts, .tsx files
  sql   .sql files
  logs  .log files
  docs  .md files
  go    .go files
  vb    .vb, .bas, .cls files
  py    .py files
  (none) all of the above, showing only sections with matches.
"""

import sys
import os
import re
import datetime
import io

# ANSI color codes
_RESET  = '\033[0m'
_BOLD   = '\033[1m'
_DIM    = '\033[2m'
_CYAN   = '\033[36m'
_YELLOW = '\033[33m'

_ANSI_RE = re.compile(r'\033\[8m.*?\033\[28m|\033\[[0-9;]*m')

CONTEXT_LINES = 5
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'search-results')
EXCLUDE_DIRS = frozenset({
    'node_modules', 'dist', 'bin', 'obj', '.vscode', '.venv', '.kiro', 
    'release', '.github', 'grafana', 'prometheus', 'e2e', 'images', 
    '.claude', 'generated', 'search-results', '.git', '.vs', '.idea', '__pycache__', 'coverage', 'logs', 'output_scripts', 'schema_export', 'docs', 'test-results', 'artifacts', 'packages', 'nuget', 'test', 'tests', 'specs', 'examples', 'sample', 'samples', 'mock', 'mocks', 'stub', 'stubs', 'backup', 'backups', 'old', 'archive', 'archives', 'temp', 'tmp', 'vendor', 'third_party', 'external'
})

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SEARCH_CONFIGS = {
    'cs': {
        'label': 'C# / Razor Files (.cs, .cshtml)',
        'paths': [REPO_ROOT],
        'extensions': ('.cs', '.cshtml'),
    },
    'js': {
        'label': 'JavaScript/TypeScript (.js, .ts, .jsx, .tsx)',
        'paths': [REPO_ROOT],
        'extensions': ('.js', '.jsx', '.ts', '.tsx'),
    },
    'sql': {
        'label': 'SQL Files (.sql)',
        'paths': [REPO_ROOT],
        'extensions': ('.sql',),
    },
    'go': {
        'label': 'Go Files (.go)',
        'paths': [REPO_ROOT],
        'extensions': ('.go',),
    },
    'vb': {
        'label': 'Visual Basic Files (.vb, .bas, .cls)',
        'paths': [REPO_ROOT],
        'extensions': ('.vb', '.bas', '.cls'),
    },
    'logs': {
        'label': 'Log Files',
        'paths': [REPO_ROOT],
        'extensions': ('.log',),
    },
    'docs': {
        'label': 'Documentation Files (.md)',
        'paths': [REPO_ROOT],
        'extensions': ('.md',),
    },
    'java': {
        'label': 'Java Files (.java)',
        'paths': [REPO_ROOT],
        'extensions': ('.java',),
    },
    'py': {
        'label': 'Python Files (.py)',
        'paths': [REPO_ROOT],
        'extensions': ('.py',),
    },
       'config': {
        'label': 'Config Files (.json, .yaml, .yml, etc.)',
        'paths': [REPO_ROOT],
        'extensions': ('.json', '.yaml', '.yml', '.env', '.ini', '.config', '.xml', '.csproj', '.vbproj', '.sln', '.props', '.targets', '.dockerfile', 'docker-compose.yml', 'docker-compose.yaml'),
    },
}

# Adjusted order to include Go and VB
SEARCH_ORDER = ('cs', 'sql', 'js', 'go', 'vb', 'py', 'logs', 'docs', 'java', 'config')

class Tee:
    def __init__(self, filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self._file = open(filepath, 'w', encoding='utf-8')
        self._stdout = sys.stdout

    def write(self, data):
        self._stdout.write(data)
        self._file.write(_ANSI_RE.sub('', data))

    def flush(self):
        self._stdout.flush()
        self._file.flush()

    def close(self):
        self._file.close()

def read_file_lines(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            return f.readlines()
    except (IOError, OSError):
        return None

def find_match_indices(lines, search_term):
    lower_term = search_term.lower()
    return [i for i, line in enumerate(lines) if lower_term in line.lower()]

def merge_context_windows(match_indices, total_lines):
    groups = []
    for idx in sorted(match_indices):
        start = max(0, idx - CONTEXT_LINES)
        end = min(total_lines - 1, idx + CONTEXT_LINES)
        if groups and start <= groups[-1][1] + 1:
            prev_start, prev_end, prev_idxs = groups[-1]
            groups[-1] = (prev_start, max(prev_end, end), prev_idxs + [idx])
        else:
            groups.append((start, end, [idx]))
    return groups

def print_file_results(filepath, lines, match_indices, search_term):
    rel_path = os.path.relpath(filepath, REPO_ROOT)
    plural = 's' if len(match_indices) != 1 else ''
    
    print(f"\n  {_BOLD}{_CYAN}{filepath}:1:{_RESET}  {_BOLD}{_CYAN}{rel_path}{_RESET}  ({len(match_indices)} match{plural})")

    match_set = set(match_indices)
    groups = merge_context_windows(match_indices, len(lines))
    term_re = re.compile(re.escape(search_term), re.IGNORECASE)

    for group_idx, (start, end, _group_matches) in enumerate(groups):
        if group_idx > 0:
            print("       ...")
        for i in range(start, end + 1):
            line_num = i + 1
            content = lines[i].rstrip('\n\r')
            if i in match_set:
                highlighted = term_re.sub(lambda m: f"{_BOLD}{_YELLOW}{m.group()}{_RESET}", content)
                print(f"  {_BOLD}{_CYAN}-->{_RESET} {_DIM}{rel_path}:{line_num}:{_RESET}")
                print(f"       {line_num}: {highlighted}")
            else:
                print(f"       {line_num}: {content}")

def collect_section(config, search_term):
    extensions = config['extensions']
    matched_files = 0
    for search_path in config['paths']:
        if not os.path.isdir(search_path):
            continue
        for root, dirs, files in os.walk(search_path):
            dirs[:] = sorted(d for d in dirs if d not in EXCLUDE_DIRS)
            for filename in sorted(files):
                if not filename.lower().endswith(extensions):
                    continue
                filepath = os.path.join(root, filename)
                lines = read_file_lines(filepath)
                if lines is None:
                    continue
                match_indices = find_match_indices(lines, search_term)
                if match_indices:
                    print_file_results(filepath, lines, match_indices, search_term)
                    matched_files += 1
    return matched_files

def run_search(search_term, file_type):
    def run_one(type_key, suppress_empty=False):
        config = SEARCH_CONFIGS[type_key]
        
        # Buffer output to check if we actually found anything before printing headers
        output_buffer = io.StringIO()
        original_stdout = sys.stdout
        sys.stdout = output_buffer
        
        try:
            count = collect_section(config, search_term)
        finally:
            sys.stdout = original_stdout

        if count > 0:
            print(f"\n{_BOLD}{'=' * 60}{_RESET}")
            print(f"  {_BOLD}{_CYAN}{config['label']}{_RESET}")
            print(f"{_BOLD}{'=' * 60}{_RESET}")
            print(output_buffer.getvalue(), end='')
        elif not suppress_empty:
            print(f"\n{_BOLD}{'=' * 60}{_RESET}")
            print(f"  {_BOLD}{_CYAN}{config['label']}{_RESET}")
            print(f"{_BOLD}{'=' * 60}{_RESET}")
            print("  No matches found.")
            
        return count

    if file_type:
        run_one(file_type, suppress_empty=False)
    else:
        total = sum(run_one(k, suppress_empty=True) for k in SEARCH_ORDER)
        if total == 0:
            print("\nNo matches found across any scope.")

def make_output_filename(search_term, file_type):
    safe_query = re.sub(r'[^\w\-]', '_', search_term)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    parts = [safe_query]
    if file_type:
        parts.append(file_type)
    parts.append(timestamp)
    return '_'.join(parts) + '.txt'

def main():
    import argparse
    parser = argparse.ArgumentParser(
        prog=os.path.basename(sys.argv[0]),
        description='INOVAR codebase search utility.',
    )
    parser.add_argument('search_term', help='String to search for (case-insensitive)')
    parser.add_argument('type', nargs='?', default=None,
                        choices=list(SEARCH_CONFIGS.keys()),
                        metavar='TYPE',
                        help='Scope: ' + ', '.join(SEARCH_ORDER) + '  (default: all)')
    parser.add_argument('--save', action='store_true',
                        help='Save output to a .txt file')
    args = parser.parse_args()

    search_term = args.search_term
    file_type = args.type.lower() if args.type else None

    tee = None
    if args.save:
        out_filename = make_output_filename(search_term, file_type)
        out_filepath = os.path.join(OUTPUT_DIR, out_filename)
        tee = Tee(out_filepath)
        sys.stdout = tee

    try:
        print(f"\nSearching for: '{search_term}'")
        if file_type:
            print(f"Scope:          {SEARCH_CONFIGS[file_type]['label']}")
        else:
            print(f"Scope:          All (filtered to matches only)")

        run_search(search_term, file_type)
        print()
    finally:
        if tee:
            sys.stdout = tee._stdout
            tee.close()

    if tee:
        print(f"Results saved to: {os.path.relpath(out_filepath)}")

if __name__ == '__main__':
    main()