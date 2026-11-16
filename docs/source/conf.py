project = 'Declan Rowley'
copyright = '2026, Declan Rowley'
author = 'Declan Rowley'
release = '0.1'

extensions = []
templates_path = ['_templates']
exclude_patterns = ['_includes', 'Thoughts.rst']

html_theme = 'basic'
html_title = 'Declan Rowley'
html_short_title = 'Declan Rowley'
html_static_path = ['_static']
html_css_files = [
    'https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@400;500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&display=swap',
    'custom.css',
]
html_js_files = [('hero.js', {'defer': 'defer'})]
html_favicon = '_static/favicon.svg'
html_extra_path = ['.nojekyll']

html_sidebars = {
    '**': [],
}

html_copy_source = False
html_domain_indices = False
html_show_copyright = False
html_show_sourcelink = False
html_show_sphinx = False
html_use_index = False
html_permalinks_icon = ''
