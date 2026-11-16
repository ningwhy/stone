// A minimal PNG reader, enough to sample pixels off a Playwright screenshot.
//
//   The project has no image library (no pngjs, no sharp), and asserting on
//   "the card picture is actually visible" cannot be done from the DOM: an
//   <img> can be perfectly loaded and still be painted with a zero-sized box,
//   and a gradient overlay can be sitting *behind* the picture instead of on
//   top of it. Both faults are invisible to the DOM and obvious to the eye.
//
//   So we take the screenshot Playwright already produced and read the pixels.
//   Only what we need is implemented: 8-bit RGB/RGBA, non-interlaced, with the
//   usual PNG filters. That covers every screenshot Chrome hands us.

import {inflateSync} from 'node:zlib';

/** Decode a PNG buffer into {width, height, data} (data is RGBA, 4 bytes/px). */
export function decodePng(buffer) {
  if (buffer.readUInt32BE(0) !== 0x89504e47) throw new Error('not a PNG');
  let pos = 8, width = 0, height = 0, bitDepth = 0, colorType = 0, interlace = 0;
  const idat = [];
  while (pos < buffer.length) {
    const length = buffer.readUInt32BE(pos);
    const type = buffer.toString('ascii', pos + 4, pos + 8);
    const body = buffer.subarray(pos + 8, pos + 8 + length);
    if (type === 'IHDR') {
      width = body.readUInt32BE(0);
      height = body.readUInt32BE(4);
      bitDepth = body[8];
      colorType = body[9];
      interlace = body[12];
    } else if (type === 'IDAT') idat.push(body);
    else if (type === 'IEND') break;
    pos += 12 + length;
  }
  if (bitDepth !== 8) throw new Error(`unsupported bit depth ${bitDepth}`);
  if (interlace !== 0) throw new Error('interlaced PNG is not supported');
  const channels = {0: 1, 2: 3, 4: 2, 6: 4}[colorType];
  if (!channels) throw new Error(`unsupported colour type ${colorType}`);

  const raw = inflateSync(Buffer.concat(idat));
  const stride = width * channels;
  const out = Buffer.alloc(height * stride);
  let prev = Buffer.alloc(stride);
  for (let y = 0; y < height; y++) {
    const filter = raw[y * (stride + 1)];
    const line = raw.subarray(y * (stride + 1) + 1, y * (stride + 1) + 1 + stride);
    const cur = out.subarray(y * stride, (y + 1) * stride);
    for (let i = 0; i < stride; i++) {
      const a = i >= channels ? cur[i - channels] : 0;
      const b = prev[i];
      const c = i >= channels ? prev[i - channels] : 0;
      const x = line[i];
      let v;
      switch (filter) {
        case 0: v = x; break;
        case 1: v = x + a; break;
        case 2: v = x + b; break;
        case 3: v = x + ((a + b) >> 1); break;
        case 4: {
          const p = a + b - c;
          const pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
          v = x + (pa <= pb && pa <= pc ? a : pb <= pc ? b : c);
          break;
        }
        default: throw new Error(`unknown filter ${filter}`);
      }
      cur[i] = v & 0xff;
    }
    prev = cur;
  }

  // Normalise to RGBA so callers have one layout to reason about.
  const rgba = Buffer.alloc(width * height * 4);
  for (let i = 0, n = width * height; i < n; i++) {
    const s = i * channels, d = i * 4;
    if (channels === 1) { rgba[d] = rgba[d + 1] = rgba[d + 2] = out[s]; rgba[d + 3] = 255; }
    else if (channels === 2) { rgba[d] = rgba[d + 1] = rgba[d + 2] = out[s]; rgba[d + 3] = out[s + 1]; }
    else if (channels === 3) { rgba[d] = out[s]; rgba[d + 1] = out[s + 1]; rgba[d + 2] = out[s + 2]; rgba[d + 3] = 255; }
    else { rgba[d] = out[s]; rgba[d + 1] = out[s + 1]; rgba[d + 2] = out[s + 2]; rgba[d + 3] = out[s + 3]; }
  }
  return {width, height, data: rgba};
}

/** Perceived brightness (0–255) of one pixel. */
export function luminance(png, x, y) {
  const i = (y * png.width + x) * 4;
  return 0.299 * png.data[i] + 0.587 * png.data[i + 1] + 0.114 * png.data[i + 2];
}

/** The darkest brightness found in one row (the text row's own ink). */
export function rowMinLuminance(png, y, x0 = 0, x1 = png.width) {
  let min = 255;
  for (let x = x0; x < x1; x++) min = Math.min(min, luminance(png, x, y));
  return min;
}

/** The brightest brightness found in one row (the backdrop the text sits on). */
export function rowMaxLuminance(png, y, x0 = 0, x1 = png.width) {
  let max = 0;
  for (let x = x0; x < x1; x++) max = Math.max(max, luminance(png, x, y));
  return max;
}
