"""Re-register new characters in the asset manifest without reformatting the file.

`build_art_assets.py` writes the whole manifest from the calibration table, so a
character that was drawn by a different pipeline would silently lose its entry.
This script re-inserts the entries for characters that were painted outside that
pipeline, using the same field layout, and leaves every other byte alone.

The `identity` block carries the face box that the album renderer crops with, so
it must carry `character` as well: `src/art.ts` types the field as required.
"""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'public/assets/rongguo/manifest.json'
ASSET_DIR = ROOT / 'public/assets/rongguo'

APPROVED = json.loads((ROOT / 'art/identity/approved.json').read_text())['assets']
DESIGNS = {c['id']: c for c in json.loads((ROOT / 'art/identity/character-designs.json').read_text())['characters']}
CALIBRATION = {a['id']: a for a in json.loads((ROOT / 'art/calibration.json').read_text())['assets']}
FACE_BOXES = json.loads((ROOT / 'art/identity/auto-face-boxes.json').read_text())

# Characters drawn by scripts/gen_new_characters.py / gen_ch20_characters.py,
# outside the calibration pipeline that owns the manifest.
NEW_CHARACTERS = ['yuanchun', 'jia_lian', 'jia_huan', 'zhao_yiniang', 'shi_xiangyun', 'she_yue']


def entry_for(character: str, kind: str) -> dict:
    key = f'{character}-{kind}'
    png = ASSET_DIR / f'{key}.png'
    if not png.exists():
        raise FileNotFoundError(png)
    from PIL import Image
    im = Image.open(png)
    cal = CALIBRATION[key]
    seed = cal['seed']
    design = DESIGNS[character]
    # The approval record is the source of truth for the painted face. When a
    # character was reviewed without an approval record (drawn straight from the
    # design sheet), the design sheet carries the same fields.
    approved = APPROVED.get(key, {})
    features = approved.get('features') or design['features']
    face_box = approved.get('faceBox') or FACE_BOXES.get(key)
    if not face_box:
        raise ValueError(f'{key}: no face box available')
    identity = {
        'character': character,
        'features': features,
        'seed': seed,
        'faceBox': list(face_box),
    }
    source = f'art/source/{key}_s{seed}-01.png'
    entry = {
        'image': f'/assets/rongguo/{key}.png',
        'width': im.width,
        'height': im.height,
        'anchor': [round(cal['anchor'][0], 3), round(cal['anchor'][1], 3)],
        'source': source,
        'matte': f'art/matted/{key}_s{seed}-sam.png',
        'crop': [0, 0, im.width, im.height],
        'shear': 0,
        'mirror': False,
        'bodyCompress': cal.get('bodyCompress'),
        'identity': identity,
    }
    return entry


def render_entry(key: str, entry: dict) -> str:
    """Render one manifest asset block in the file's own formatting."""
    identity = entry['identity']
    body = json.dumps(entry, ensure_ascii=False, indent=1)
    # The face box is written inline like the rest of the reviewed identities so
    # the diff stays about content rather than indentation.
    body = re.sub(
        r'"identity": \{.*?\}',
        '"identity": {"character": "%s", "features": %s, "seed": %s, "faceBox": %s}'
        % (identity['character'], json.dumps(identity['features'], ensure_ascii=False),
           identity['seed'], json.dumps(identity['faceBox'])),
        body, flags=re.S)
    return f'  {json.dumps(key)}: {body}'


def main() -> None:
    text = MANIFEST.read_text()
    manifest = json.loads(text)
    assets = manifest['assets']

    added = []
    for character in NEW_CHARACTERS:
        for kind in ('portrait', 'chibi'):
            key = f'{character}-{kind}'
            entry = entry_for(character, kind)
            block = render_entry(key, entry)
            pattern = re.compile(r'  "%s": \{.*?\n  \},?\n' % re.escape(key), re.S)
            if pattern.search(text):
                text = pattern.sub(block + ',\n', text, count=1)
            else:
                # Append after the last asset so the closing brace stays last.
                marker = '\n }\n}'
                index = text.rindex(marker)
                text = text[:index] + ',\n' + block + text[index:]
            assets[key] = entry
            added.append(key)

    MANIFEST.write_text(text)
    # Verify the result still parses and that every identity kept its character.
    reloaded = json.loads(MANIFEST.read_text())['assets']
    broken = [k for k, v in reloaded.items()
              if v.get('identity') and 'character' not in v['identity']]
    if broken:
        raise SystemExit(f'identity block without character: {broken}')
    print(f'manifest: registered {len(added)} assets ({", ".join(added)}); '
          f'{len(reloaded)} assets total; every identity carries a character')


if __name__ == '__main__':
    main()
