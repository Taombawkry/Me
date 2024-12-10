import markdown
import os
from pathlib import Path

def read_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def convert_markdown_to_html():
    # Create markdown converter
    md = markdown.Markdown()
    
    # Read template
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
    
    # Convert each markdown file to HTML
    sections = {}
    content_dir = Path('content')
    for md_file in content_dir.glob('*.md'):
        section_name = md_file.stem  # Get filename without extension
        markdown_content = read_file(md_file)
        html_content = md.convert(markdown_content)
        sections[section_name] = html_content
    
    # Read CSS
    css = read_file('styles.css')
    
    # Create the final HTML using string formatting
    final_html = template % (
        css,
        sections.get('header', ''),
        sections.get('about', ''),
        sections.get('social', ''),
        sections.get('writings', ''),
        sections.get('email', ''),
        sections.get('schedule', '')
    )
    
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)
    
    # Write the final HTML file
    write_file('output/index.html', final_html)

if __name__ == '__main__':
    convert_markdown_to_html()