

## Features
- Content written in Markdown for easy editing and maintenance
- YAML frontmatter support for metadata and content organization
- HackMD integration for content management and CDN functionality
- Pure HTML/CSS output with no JavaScript dependencies
- Monospace typography and clean design
- Mobile-responsive layout

## Structure
```
website/
├── content/         # Markdown files for each section
├── build.py         # Python script to generate static site
├── styles.css       # CSS styling
└── output/          # Generated static site
```

## Content Management
Content is written in Markdown with YAML frontmatter. Files are hosted on HackMD for easy updates and CDN functionality. Example:
```markdown
---
title: "Writings"
date: 2024-12-10
tags: ["website", "blog", "essays"]
---

# Section Content
...
```

## Local Development
1. Install dependencies: `pip install markdown pyyaml`
2. Edit content in `content/` directory
3. Run `python build.py` to generate site
4. Deploy `output/` directory

## Deployment
Site is deployed using Netlify with automatic builds triggered by Git pushes.
