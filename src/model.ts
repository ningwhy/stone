export type Point = { col: number; row: number };
/** `indoor` marks a floor that belongs to a building's interior rather than open ground. */
export type Zone = { id: string; name: string; col: number; row: number; width: number; height: number; indoor?: boolean };
/** `interiorZone` on an `exterior` art names the floor it roofs over, so the roof can be
 *  lifted the moment somebody walks in without any per-scene script bookkeeping. */
export type ArtObject = { name:string; asset:string; x:number; y:number; width:number; height:number; visibility:string; depthOffset:number; interiorZone?: string };
export type MapData = {
  width: number; height: number; tilewidth: number; tileheight: number;
  anchors: Record<string, Point>; zones: Zone[]; blockers: Zone[];
  routes: Record<string, string[]>; walkable: Set<string>;
  art: ArtObject[];
  id:string; title:string; theme:string; labels:{text:string;point:Point}[];
  /** `water` lists the canal or pond rectangles (col,row,w,h in grid units) a river stage
   *  paints over the floor. A stage without it keeps the historic garden pond rectangle. */
  water: [number,number,number,number][];
  /** The estate flowerbeds are a Rongguo-garden ornament; a stage whose floor they would
   *  paint over (a canal, say) turns them off instead of moving them per scene. */
  flowerbeds: boolean;
};
export const cellKey = (col: number, row: number) => `${col},${row}`;

/** The floor region a fractional grid position stands on, if any. */
export function zoneAt(map: MapData, col: number, row: number): Zone | undefined {
  return map.zones.find(z => col >= z.col && col < z.col + z.width && row >= z.row && row < z.row + z.height);
}

type TiledObject = { name: string; x: number; y: number; width: number; height: number; rotation?:number; visible?:boolean; gid?:number; properties?: {name: string; value: unknown}[] };
type TiledMap = {
  orientation: string; width: number; height: number; tilewidth: number; tileheight: number;
  properties?:{name:string;value:unknown}[];
  layers: { name: string; objects?: TiledObject[] }[];
};

export function parseTiledMap(raw: TiledMap): MapData {
  if (raw.orientation !== 'isometric' || raw.tilewidth !== raw.tileheight * 2) throw new Error('地图需要使用 2:1 普通等距视角');
  const objects = (name: string) => {
    const layer = raw.layers.find(l => l.name === name);
    if (!layer?.objects) throw new Error(`缺少 Tiled 对象层：${name}`);
    return layer.objects;
  };
  const unit = raw.tileheight;
  const anchors: Record<string, Point> = {};
  for (const o of objects('Anchors')) {
    const col = o.x / unit - 0.5, row = o.y / unit - 0.5;
    if (Math.abs(col - Math.round(col)) > .01 || Math.abs(row - Math.round(row)) > .01) throw new Error(`地点 ${o.name} 需要位于格心`);
    if (col < 0 || row < 0 || col >= raw.width || row >= raw.height || anchors[o.name]) throw new Error(`地点无效或重复：${o.name}`);
    anchors[o.name] = { col: Math.round(col), row: Math.round(row) };
  }
  const boolProp = (o: TiledObject, name: string) => { const v = o.properties?.find(p => p.name === name)?.value; return v === true || v === 'true'; };
  const zones = (layer: string) => objects(layer).map(o => ({ id: o.name.split(' ')[0], name: o.name.slice(2), col: o.x / unit, row: o.y / unit, width: o.width / unit, height: o.height / unit, indoor: boolProp(o, 'indoor') || undefined }));
  // A stage may declare its own water rectangles as "col,row,w,h;col,row,w,h" and switch the
  // estate flowerbeds off; both fall back to the historic garden look when the property is absent.
  const waterProp = raw.properties?.find(p => p.name === 'water')?.value;
  const water: [number,number,number,number][] = typeof waterProp === 'string' && waterProp.trim()
    ? waterProp.split(';').map(part => part.split(',').map(Number) as [number,number,number,number])
    : [];
  const flowerProp = raw.properties?.find(p => p.name === 'flowerbeds')?.value;
  const flowerbeds = !(flowerProp === false || flowerProp === 'false');
  const map: MapData = { width: raw.width, height: raw.height, tilewidth: raw.tilewidth, tileheight: unit,
    anchors, zones: zones('PlanZones'), blockers: zones('PlanBlockers'), routes: {}, walkable: new Set(), art: [],id:String(raw.properties?.find(p=>p.name==='sceneId')?.value??'entry'),title:String(raw.properties?.find(p=>p.name==='title')?.value??'荣国府 · 贾母院'),theme:String(raw.properties?.find(p=>p.name==='theme')?.value??'garden'),labels:[],water,flowerbeds };
  for(const o of raw.layers.find(l=>l.name==='Labels')?.objects??[])map.labels.push({text:o.name,point:{col:o.x/unit-.5,row:o.y/unit-.5}});
  for(const o of raw.layers.find(l=>l.name==='Art')?.objects??[]) {
    if(o.visible===false)continue;
    if(o.rotation || (o.gid??0)>0x0fffffff)throw new Error(`素材 ${o.name} 暂不支持旋转或 Tiled 翻转，请使用校准后的变体`);
    const prop=(name:string)=>o.properties?.find(p=>p.name===name)?.value;
    const asset=prop('asset');
    if(typeof asset!=='string' || o.width<=0 || o.height<=0)throw new Error(`素材 ${o.name} 缺少有效图像与尺寸`);
    map.art.push({name:o.name,asset,x:o.x-o.y,y:(o.x+o.y)/2,width:o.width,height:o.height,visibility:String(prop('visibility')??'always'),depthOffset:Number(prop('depthOffset')??0),interiorZone:typeof prop('interiorZone')==='string'?String(prop('interiorZone')):undefined});
  }
  for(const o of raw.layers.find(l=>l.name==='ArtFootprints')?.objects??[])map.blockers.push({id:o.name,name:o.name,col:o.x/unit,row:o.y/unit,width:o.width/unit,height:o.height/unit});
  for (const o of objects('Routes')) {
    const prop = (name: string) => o.properties?.find(p => p.name === name)?.value;
    const id = prop('route_id'), names = prop('anchor_ids');
    if (typeof id !== 'string' || typeof names !== 'string') throw new Error(`路线 ${o.name} 缺少 route_id / anchor_ids`);
    map.routes[id] = names.split(',');
    for (const name of map.routes[id]) if (!anchors[name]) throw new Error(`路线 ${id} 引用了不存在的地点 ${name}`);
  }
  // Prototype floors are explicit design zones, not inferred from decorative artwork.
  for (const z of map.zones.filter(z => /^(A\d*|B|C|D|E|F)$/.test(z.id))) {
    for (let c = z.col; c < z.col + z.width; c++) for (let r = z.row; r < z.row + z.height; r++) map.walkable.add(cellKey(c, r));
  }
  // Connect gaps between floor regions using the Tiled route's guide corridor.
  for (const route of Object.values(map.routes)) {
    for (let i = 1; i < route.length; i++) {
      const from = anchors[route[i-1]], to = anchors[route[i]];
      let c = from.col, r = from.row;
      map.walkable.add(cellKey(c, r));
      while (c !== to.col) { c += Math.sign(to.col-c); map.walkable.add(cellKey(c, r)); }
      while (r !== to.row) { r += Math.sign(to.row-r); map.walkable.add(cellKey(c, r)); }
    }
  }
  for (const b of map.blockers) for (let c = b.col; c < b.col+b.width; c++) for (let r = b.row; r < b.row+b.height; r++) map.walkable.delete(cellKey(c,r));
  return map;
}

/** Cardinal A*: no diagonal corner cutting through walls or the screen. */
export function findPath(map: MapData, start: Point, end: Point): Point[] {
  const from = { col: Math.round(start.col), row: Math.round(start.row) };
  const target = cellKey(end.col, end.row), first = cellKey(from.col, from.row);
  if (!map.walkable.has(first) || !map.walkable.has(target)) throw new Error(`起点或目标不可通行：${first} → ${target}`);
  const heuristic = (p: Point) => Math.abs(p.col-end.col)+Math.abs(p.row-end.row);
  const open = new Map<string, Point>([[first, from]]), parents = new Map<string, string>();
  const cost = new Map([[first, 0]]);
  while (open.size) {
    let key = '', best = Infinity, current = from;
    for (const [k, p] of open) {
      const score = cost.get(k)! + heuristic(p);
      if (score < best) { key = k; best = score; current = p; }
    }
    if (key === target) {
      const path: Point[] = [];
      let cursor: string | undefined = key;
      while (cursor) { const [col,row] = cursor.split(',').map(Number); path.unshift({col,row}); cursor = parents.get(cursor); }
      return path;
    }
    open.delete(key);
    for (const [dc,dr] of [[0,-1],[-1,0],[1,0],[0,1]]) {
      const point = {col: current.col+dc, row: current.row+dr}, next = cellKey(point.col, point.row);
      if (!map.walkable.has(next)) continue;
      const nextCost = cost.get(key)!+1;
      if (nextCost >= (cost.get(next) ?? Infinity)) continue;
      parents.set(next, key); cost.set(next, nextCost); open.set(next, point);
    }
  }
  throw new Error(`没有可行走路线：${first} → ${target}`);
}

export function project(point: Point, map: Pick<MapData,'tilewidth'|'tileheight'>) {
  return { x: (point.col-point.row)*map.tilewidth/2, y: (point.col+point.row+1)*map.tileheight/2 };
}
