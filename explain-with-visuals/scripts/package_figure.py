#!/usr/bin/env python3
"""Package an authored figure and optional replay as portable HTML."""

import argparse
import html
import json
from pathlib import Path
import re
import tempfile
import uuid
import xml.etree.ElementTree as ET


def namespace_ids(markup, prefix):
    """Keep SVG definitions and accessibility references local to one figure."""
    ids = re.findall(r'(?<![\w:-])id\s*=\s*[\"\']([^\"\']+)[\"\']', markup)
    if len(ids) != len(set(ids)):
        raise ValueError('The figure contains duplicate IDs.')
    mapping = {identifier: f'{prefix}-{identifier}' for identifier in ids}

    def replace_id(match):
        return f'{match[1]}{match[2]}{mapping[match[3]]}{match[2]}'

    markup = re.sub(r'((?<![\w:-])id\s*=\s*)([\"\'])([^\"\']+)\2', replace_id, markup)
    for old, new in mapping.items():
        markup = re.sub(r'url\(\s*([\"\']?)#' + re.escape(old) + r'\1\s*\)',
                        f'url(#{new})', markup)
        markup = re.sub(r'((?<![\w:-])(?:href|xlink:href)\s*=\s*[\"\'])#' + re.escape(old) + r'([\"\'])',
                        lambda match: match[1] + '#' + new + match[2], markup)

    def replace_labels(match):
        tokens = match[3].split()
        value = ' '.join(mapping.get(token, token) for token in tokens)
        return f'{match[1]}{match[2]}{value}{match[2]}'

    return re.sub(r'((?<![\w:-])(?:aria-labelledby|aria-describedby|for)\s*=\s*)([\"\'])([^\"\']+)\2',
                  replace_labels, markup)


def inline_script(source):
    return re.sub(r'</script', r'<\/script', source, flags=re.IGNORECASE)


def build(args):
    skill_root = Path(__file__).resolve().parent.parent
    figure_path = args.figure.resolve()
    output = args.output.resolve()
    inputs = [figure_path]
    if args.scene:
        inputs.append(args.scene.resolve())
    if args.style:
        inputs.append(args.style.resolve())
    if output in inputs:
        raise ValueError('Choose an output path distinct from the source files.')

    graphic = figure_path.read_text(encoding='utf-8').strip()
    if figure_path.suffix.lower() == '.svg':
        svg = ET.fromstring(graphic)
        if svg.tag.rsplit('}', 1)[-1] != 'svg':
            raise ValueError('An SVG source must have an svg root.')
        if not svg.get('viewBox'):
            raise ValueError('Add a responsive viewBox to the SVG.')
        graphic = re.sub(r'^<\?xml[^>]*>\s*', '', graphic)
    if re.search(r'<\s*(script|style|html|head|body)\b', graphic, re.IGNORECASE):
        raise ValueError('Use a figure fragment with styles and scripts supplied separately.')

    root_id = args.id or f'figure-{uuid.uuid4().hex[:12]}'
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', root_id):
        raise ValueError('The figure ID must start with a letter and use letters, digits, _ or -.')
    graphic = namespace_ids(graphic, root_id)
    css = (skill_root / 'assets' / 'figure.css').read_text(encoding='utf-8')
    if args.style:
        css += '\n' + args.style.read_text(encoding='utf-8')
    css = css.replace('__ROOT__', f'#{root_id}')
    if re.search(r'</style', css, re.IGNORECASE):
        raise ValueError('CSS must not contain a closing style tag.')

    caption = html.escape(args.caption or '')
    title = html.escape(args.title)
    fragment = f'''<style>{css}</style>
<figure id="{root_id}" aria-label="{title}">
  <div data-stage>{graphic}</div>
  <div data-controls hidden></div>
  <figcaption data-caption aria-live="polite">{caption}</figcaption>
</figure>'''
    if args.scene:
        player = (skill_root / 'assets' / 'player.js').read_text(encoding='utf-8')
        scene = args.scene.read_text(encoding='utf-8')
        initialization = f'''
const figureRoot = document.getElementById({json.dumps(root_id)});
try {{
  mountVisualPlayer(figureRoot, createScene(figureRoot));
}} catch (error) {{
  figureRoot.querySelector('[data-caption]').textContent = `Unable to initialize this figure. ${{error.message}}`;
  console.error(error);
}}
'''
        fragment += '\n<script>\n(() => {\n' + inline_script(player + '\n' + scene + initialization) + '\n})();\n</script>'

    result = fragment
    if args.format == 'standalone':
        result = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>body {{ margin: 0; }} main {{ max-width: 1100px; margin: auto; }}</style>
</head>
<body><main>{fragment}</main></body>
</html>
'''
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=output.parent,
                                         prefix=f'.{output.name}.', delete=False) as temporary:
            temporary.write(result)
            temporary_path = Path(temporary.name)
        temporary_path.replace(output)
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()
    print(json.dumps({'output': str(output), 'figure_id': root_id, 'format': args.format,
                      'interactive': bool(args.scene)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--figure', type=Path, required=True, help='SVG or HTML stage fragment')
    parser.add_argument('--scene', type=Path, help='JavaScript defining createScene(root)')
    parser.add_argument('--style', type=Path, help='CSS with __ROOT__ as the root selector')
    parser.add_argument('--title', required=True)
    parser.add_argument('--caption')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--format', choices=['standalone', 'fragment'], default='standalone')
    parser.add_argument('--id', help='Optional unique figure ID')
    args = parser.parse_args()
    try:
        build(args)
    except (ValueError, OSError, ET.ParseError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
