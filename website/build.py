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
    template = read_file('template.html')
    
    # Initialize content sections
    sections = {}
    
    # Convert each markdown file to HTML
    content_dir = Path('content')
    for md_file in content_dir.glob('*.md'):
        section_name = md_file.stem  # Get filename without extension
        markdown_content = read_file(md_file)
        html_content = md.convert(markdown_content)
        sections[section_name] = html_content
    
    # Read CSS
    css = read_file('styles.css')
    
    # Replace placeholders in template
    final_html = template
    for section_name, content in sections.items():
        placeholder = f'{{{{ {section_name} }}}}'
        final_html = final_html.replace(placeholder, content)
    
    # Replace CSS placeholder
    final_html = final_html.replace('{{ styles }}', css)
    
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)
    
    # Write the final HTML file
    write_file('output/index.html', final_html)

if __name__ == '__main__':
    convert_markdown_to_html()