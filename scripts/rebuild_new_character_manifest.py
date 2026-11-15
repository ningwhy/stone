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
NEW_CHARACTERS = ['yuanchun', 'jia_lian', 'jia_huan', 'zhao_yiniang', 'shi_xiangyun', 'she_yue',
                  'zijun', 'cui_lv', 'si_er', 'jia_lan',
                  'jinyuan', 'caiyun', 'jia_qin']


def final_anchor(key: str, entry: dict, cal: dict):
    """The feet anchor expressed in the **final PNG's** pixel coordinates.

    `art/calibration.json` stores the anchor where it was measured — on the
    raw matte, before the crop and the scale. The bitmap the browser loads is
    the cropped-and-scaled one, so the raw value lands outside the picture:
    `jia_lan-portrait` carried an anchor of (227, 1130) on a 385x600 bitmap,
    which is 530 pixels below the feet.

    The transform is the one `scripts/map_facebox_to_final.py` replays:

      1. `bodyCompress` squeezes everything below `split` by `factor`, so the
         anchor moves up with it,
      2. the picture is cropped to its opaque bounding box, which shifts the
         anchor up and left,
      3. the result is scaled to the calibrated height.

    Steps 1-3 are affine, so the anchor can be carried through exactly.
    """
    from PIL import Image

    matte_path = ROOT / entry['matte']
    im = Image.open(matte_path).convert('RGBA')

    import numpy as np

    ax, ay = cal['anchor']
    if cal.get('bodyCompress'):
        split = cal['bodyCompress']['split']
        factor = cal['bodyCompress']['factor']
        lower = im.crop((0, split, im.width, im.height)).resize(
            (im.width, round((im.height - split) * factor)), Image.Resampling.LANCZOS)
        joined = Image.new('RGBA', (im.width, split + lower.height))
        joined.paste(im.crop((0, 0, im.width, split)), (0, 0))
        joined.paste(lower, (0, split))
        im = joined
        if ay > split:
            ay = split + (ay - split) * factor

    # The crop starts at the first *solid* pixel: `build_art_assets.py` binarises
    # the alpha at 110 and crops to that box, then scales the crop to the
    # calibrated height. Measuring the whole canvas instead puts the anchor
    # 400px out on a 214px bitmap. The box is measured **after** the compression,
    # because the compression moves the lower body up and changes the extent.
    alpha = np.asarray(im.getchannel('A'))
    solid = np.where(alpha >= 110, 255, 0).astype('uint8')
    rows = np.where(solid.max(axis=1) > 0)[0]
    cols = np.where(solid.max(axis=0) > 0)[0]
    if len(rows) == 0 or len(cols) == 0:
        raise ValueError(f'{key}: blank matte')
    bbox = (int(cols.min()), int(rows.min()), int(cols.max()) + 1, int(rows.max()) + 1)
    cropped_w = bbox[2] - bbox[0]
    cropped_h = bbox[3] - bbox[1]
    factor = cal['width'] / cropped_w if 'width' in cal else cal['height'] / cropped_h
    size = (round(cropped_w * factor), round(cropped_h * factor))
    sx = size[0] / cropped_w
    sy = size[1] / cropped_h
    return (ax - bbox[0]) * sx, (ay - bbox[1]) * sy


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
        'anchor': [0, 0],
        'source': source,
        'matte': f'art/matted/{key}_s{seed}-sam.png',
        'crop': [0, 0, im.width, im.height],
        'shear': 0,
        'mirror': False,
        'bodyCompress': cal.get('bodyCompress'),
        'identity': identity,
    }
    ax, ay = final_anchor(key, entry, cal)
    entry['anchor'] = [round(ax, 3), round(ay, 3)]
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
