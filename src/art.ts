import manifest from '../public/assets/rongguo/manifest.json' with { type: 'json' };
import type { ArtObject } from './model.ts';

export const artAssets: Record<string,{image:string;width:number;height:number;anchor:number[];identity?:{character:string;features:string;seed:number;faceBox:number[];revision:string;source:string}}> = manifest.assets;

/** Identity revision invalidates cached portraits and Phaser textures after an art rebuild. */
export function artImage(key:string) {
  const asset=artAssets[key];
  return asset.identity?`${asset.image}?v=${asset.identity.revision}`:asset.image;
}

/** Tiled bottom-centre image objects and Phaser use the same image-bottom point.
 * The gameplay anchor is an independent measured point within the bitmap. */
export function artGround(object:ArtObject) {
  const asset=artAssets[object.asset];
  if(!asset)throw new Error(`未知素材：${object.asset}`);
  return {x:object.x+(asset.anchor[0]-asset.width/2)*object.width/asset.width,
    y:object.y+(asset.anchor[1]-asset.height)*object.height/asset.height};
}
