import manifest from '../public/assets/rongguo/manifest.json' with { type: 'json' };
import type { ArtObject } from './model.ts';

export const artAssets: Record<string,{image:string;width:number;height:number;anchor:number[];hash?:string;identity?:{character:string;features:string;seed:number;faceBox:number[];revision:string;source:string}}> = manifest.assets;

/** Identity revision invalidates cached portraits and Phaser textures after an art rebuild.
 * The manifest keeps the PNG originals as source of truth for calibration and content checks;
 * scripts/build_webp.mjs ships WebP siblings (committed to the repo), and the runtime
 * requests WebP exclusively. Regenerate with `npm run art:webp` after an art rebuild.
 *
 * `hash` is the WebP's own content digest, written by build_webp.mjs. It is the cache
 * key for props and furniture too: without it a rebuilt asset kept its old URL and
 * browsers served the stale bitmap from cache — the sedan grew four bearers and the
 * page still showed the empty chair. Identity revision is the fallback for any entry
 * written before hashes existed. */
export function artImage(key:string) {
  const asset=artAssets[key];
  const image=asset.image.replace(/\.png$/,'.webp');
  const version=asset.hash??asset.identity?.revision;
  return version?`${image}?v=${version}`:image;
}

/** The production build prunes PNG originals, so every runtime reference must ask for the
 * WebP sibling. Callers that already hold an asset record use this instead of `.image`. */
export function assetImage(asset:{image:string;hash?:string;identity?:{revision:string}}):string {
  const image=asset.image.replace(/\.png$/,'.webp');
  const version=asset.hash??asset.identity?.revision;
  return version?`${image}?v=${version}`:image;
}

/** Tiled bottom-centre image objects and Phaser use the same image-bottom point.
 * The gameplay anchor is an independent measured point within the bitmap. */
export function artGround(object:ArtObject) {
  const asset=artAssets[object.asset];
  if(!asset)throw new Error(`未知素材：${object.asset}`);
  return {x:object.x+(asset.anchor[0]-asset.width/2)*object.width/asset.width,
    y:object.y+(asset.anchor[1]-asset.height)*object.height/asset.height};
}
