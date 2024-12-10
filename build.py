import markdown
import os
from pathlib import Path
import yaml 
import json
from datetime import date, datetime

def parse_markdown_with_frontmatter(content):
    """Parse markdown content with YAML frontmatter"""
    # Check if content starts with frontmatter delimiter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            # Parse the YAML frontmatter
            try:
                frontmatter = yaml.safe_load(parts[1])
                # Return the frontmatter and the remaining markdown content
                return frontmatter, parts[2]
            except yaml.YAMLError as e:
                print(f"Error parsing frontmatter: {e}")
                return {}, content
    return {}, content

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle dates"""
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)

def create_initial_files():
    """Create the initial directory structure and files if they don't exist"""
    # Create directories
    os.makedirs('content', exist_ok=True)
    os.makedirs('output', exist_ok=True)
    
    # Create styles.css if it doesn't exist
    if not os.path.exists('styles.css'):
        with open('styles.css', 'w', encoding='utf-8') as f:
            f.write("""body {
    font-family: 'Courier New', Courier, monospace;
    margin: 0 auto;
    padding: 0;
    line-height: 1.6;
    text-align: center;
    max-width: 800px;
    background: #ffffff;
    color: #1a1a1a;
}

header {
    padding: 2rem 0;
    border-bottom: 1px solid #e0e0e0;
}

header h1 {
    font-size: 2rem;
    font-weight: normal;
    margin: 0;
}

nav ul {
    list-style: none;
    padding: 1rem 0;
    margin: 0;
    display: flex;
    justify-content: center;
    background: #fff;
    flex-wrap: wrap;
    border-bottom: 1px solid #e0e0e0;
}

nav ul li {
    margin: 0 1rem;
}

nav ul li a {
    text-decoration: none;
    padding: 0.5rem;
    display: block;
    color: #1a1a1a;
    font-size: 0.9rem;
}

nav ul li a:hover {
    text-decoration: underline;
    background: #f5f5f5;
}

section {
    padding: 2rem;
    margin: 1rem 0;
    text-align: left;
    border-bottom: 1px solid #e0e0e0;
}

section:last-child {
    border-bottom: none;
}

section h2 {
    font-size: 1.5rem;
    font-weight: normal;
    margin-top: 0;
    margin-bottom: 1.5rem;
    color: #333;
}

ul {
    list-style: none;
    padding: 0;
}

ul li {
    margin: 0.75rem 0;
    line-height: 1.5;
}

a {
    color: #0066cc;
    text-decoration: none;
    padding: 0.1rem 0.2rem;
}

a:hover {
    text-decoration: underline;
    background: #f0f0f0;
}

p {
    margin: 1rem 0;
}

@media (max-width: 768px) {
    body {
        padding: 0 1rem;
    }
    
    nav ul {
        flex-direction: column;
    }
    
    section {
        padding: 1rem 0;
    }
    
    nav ul li {
        margin: 0.5rem 0;
    }
    
    nav ul li a {
        padding: 0.5rem;
        font-size: 1rem;
    }
}""")
                # Create initial markdown files if they don't exist
    sections = ['header', 'about', 'social', 'writings', 'email', 'schedule']
    for section in sections:
        filepath = f'content/{section}.md'
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f'## {section.title()}\n\nAdd your content here.')

def read_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Could not find {filepath}")
        return ""
    except Exception as e:
        print(f"Error reading {filepath}: {str(e)}")
        return ""

def write_file(filepath, content):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"Error writing to {filepath}: {str(e)}")

def convert_markdown_to_html():
    print("Starting website generation...")
    
    # Create initial files if they don't exist
    create_initial_files()
    print("Created initial files and directories...")
    
    # Create markdown converter
    md = markdown.Markdown(extensions=['meta'])
    
    # Convert each markdown file to HTML
    sections = {}
    metadata = {}  # Store metadata for each section
    content_dir = Path('content')
    
    for md_file in content_dir.glob('*.md'):
        section_name = md_file.stem
        print(f"Converting {md_file}...")
        
        # Read and parse the markdown content
        content = read_file(md_file)
        frontmatter, markdown_content = parse_markdown_with_frontmatter(content)
        
        # store metadata
        if frontmatter:
            metadata[section_name] = frontmatter
        
        # convert to HTML
        html_content = md.convert(markdown_content)
        sections[section_name] = html_content
    
    # read CSS
    print("Reading CSS...")
    css = read_file('styles.css')
    
    # create the final HTML
    print("Generating final HTML...")
    template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thomas Gondwe - Personal Website</title>
    <style type="text/css">
%s
    </style>
</head>
<body>
    <header>
        %s
    </header>
    <nav>
        <ul>
            <li><a href="#about">About Me</a></li>
            <li><a href="#social-links">Social Links</a></li>
            <li><a href="#writings">Writings</a></li>
            <li><a href="#email">Email</a></li>
            <li><a href="#schedule-call">Schedule a Call</a></li>
        </ul>
    </nav>
    <section id="about">
        %s
    </section>
    <section id="social-links">
        %s
    </section>
    <section id="writings">
        %s
    </section>
    <section id="email">
        %s
    </section>
    <section id="schedule-call">
        %s
    </section>
</body>
</html>"""
    
    final_html = template % (
        css,
        sections.get('header', ''),
        sections.get('about', ''),
        sections.get('social', ''),
        sections.get('writings', ''),
        sections.get('email', ''),
        sections.get('schedule', '')
    )
    
    # write the final HTML file
    print("Writing output file...")
    write_file('output/index.html', final_html)
    
    if metadata:
        metadata_json = json.dumps(metadata, indent=2, cls=CustomJSONEncoder)
        write_file('output/metadata.json', metadata_json)
    
    print("Website generation complete! Check the output/index.html file.")

if __name__ == '__main__':
    convert_markdown_to_html()