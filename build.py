#!/usr/bin/env python3
"""
build.py — a minimalist orchestrator that:
  1. Reads content/
  2. Converts Markdown → HTML via Markdown+mermaid2
  3. Renders with Jinja2 templates
"""
import os
import shutil
import yaml
import json
import re
from pathlib import Path
from datetime import datetime, date
from markdown import Markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Paths
CONTENT_DIR = Path('content')
OUTPUT_DIR  = Path('output')
TEMPLATES   = FileSystemLoader('templates')
env = Environment(
    loader=TEMPLATES,
    autoescape=select_autoescape(['html'])
)

# Initialize Markdown with mermaid
md = Markdown(extensions=[
    'meta',
    'fenced_code',
    'codehilite',
    'markdown_mermaid'   
])

def clean_output():
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

def load_markdown(path: Path):
    text = path.read_text(encoding='utf-8')
    if text.startswith('---'):
        _, fm, body = text.split('---', 2)
        try:
            front = yaml.safe_load(fm)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML frontmatter in {path}: {e}")
            front = {}
    else:
        front, body = {}, text
    html = md.convert(body)
    md.reset()  # clear metadata for next file
    return front, html

def clean_html(html):
    """Remove HTML tags and clean up whitespace"""
    clean = re.sub(r'<[^>]+>', '', html)
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()

def build_blog():
    """
    Process blog posts and render them.
    Robustly parse frontmatter dates (date, datetime, or ISO string).
    """
    posts = []
    categories = {}

    # Iterate over each category folder under content/blog
    for cat_dir in (CONTENT_DIR / 'blog').iterdir():
        if not cat_dir.is_dir():
            continue

        for md_file in cat_dir.glob('*.md'):
            # Load frontmatter and HTML
            fm, html = load_markdown(md_file)

            # ==== Robust date parsing ====
            raw_date = fm.get('date', None)
            if isinstance(raw_date, datetime):
                date_obj = raw_date
            elif isinstance(raw_date, date):
                # combine date with midnight time
                date_obj = datetime.combine(raw_date, datetime.min.time())
            elif isinstance(raw_date, str):
                try:
                    date_obj = datetime.fromisoformat(raw_date)
                except ValueError:
                    # fallback if string isn't ISO
                    date_obj = datetime.now()
            else:
                date_obj = datetime.now()
            # ==============================

            # Clean excerpt
            excerpt = clean_html(html)[:150] + '…'

            # Build the post dict
            post = {
                'title': fm.get('title', md_file.stem),
                'description': fm.get('description', ''),   
                'date': date_obj,
                'category': cat_dir.name,
                'tags': fm.get('tags', []),
                'excerpt': excerpt,
                'content': html,
                'slug': md_file.stem,
                'link': f"{cat_dir.name}/{md_file.stem}.html"  # Removed blog/ prefix
            }

            posts.append(post)
            categories.setdefault(cat_dir.name, []).append(post)

    # Sort posts newest-first
    posts.sort(key=lambda p: p['date'], reverse=True)
    for cat_posts in categories.values():
        cat_posts.sort(key=lambda p: p['date'], reverse=True)

    # Add prev/next links to posts
    for i, post in enumerate(posts):
        post['prev'] = posts[i + 1] if i < len(posts) - 1 else None
        post['next'] = posts[i - 1] if i > 0 else None

    # Render each post with Jinja2 post.html
    tmpl = env.get_template('post.html')
    for post in posts:
        outpath = OUTPUT_DIR / 'blog' / post['link']  # Added blog/ here instead
        outpath.parent.mkdir(parents=True, exist_ok=True)
        rendered = tmpl.render(
            title=post['title'],
            post=post,
            home_link='../../index.html',
            blog_link='../../blog/index.html',
            css_path='../../styles.css'
        )
        outpath.write_text(rendered, encoding='utf-8')

    # ——— Render the main blog index ———
    bi = env.get_template('blog_index.html')
    blog_index_html = bi.render(
        title="Blog",
        posts=posts,
        categories=[
            {'name': name, 'link': f"category/{name}.html"} 
            for name in categories
        ],
        index_link="index.html",
        category=None,
        home_link="../index.html",
        blog_link="index.html",
        css_path="../styles.css"
    )
    # write it out
    (OUTPUT_DIR / 'blog').mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / 'blog' / 'index.html').write_text(blog_index_html, encoding='utf-8')

    # ——— Render each category page ———
    for name, cat_posts in categories.items():
        cat_html = bi.render(
            title=f"Blog — {name.title()}",
            posts=cat_posts,
            categories=[
                {'name': n, 'link': f"{n}.html"} 
                for n in categories
            ],
            index_link="../index.html",
            category=name,
            home_link="../../index.html",  # Fixed path
            blog_link="../index.html",     # Fixed path
            css_path="../../styles.css"    # Fixed path
        )
        outpath = OUTPUT_DIR / 'blog' / 'category' / f"{name}.html"
        outpath.parent.mkdir(parents=True, exist_ok=True)
        outpath.write_text(cat_html, encoding='utf-8')


def build_site():
    clean_output()
    # Copy static assets
    shutil.copy('styles.css', OUTPUT_DIR / 'styles.css')
    if Path('blog-styles.css').exists():
        shutil.copy('blog-styles.css', OUTPUT_DIR / 'blog-styles.css')
    else:
        print("Warning: 'blog-styles.css' not found. Skipping copy.")
    # Build main sections
    sections = {p.stem: load_markdown(p) for p in CONTENT_DIR.glob('*.md')}
    base_tmpl = env.get_template('index.html')
    html = base_tmpl.render(
        title="Thomas Gondwe",
        css_path='styles.css',
        **{ name: content for name, (_, content) in sections.items() }
    )
    (OUTPUT_DIR / 'index.html').write_text(html, encoding='utf-8')
    # Blog
    build_blog()
    print("✨ Build complete — check output/index.html")

if __name__ == '__main__':
    build_site()
