export type Point = { col: number; row: number };
/** `indoor` marks a floor that belongs to a building's interior rather than open ground. */
export type Zone = { id: string; name: string; col: number; row: number; width: number; height: number; indoor?: boolean };
/** `interiorZone` on an `exterior` art names the floor it roofs over, so the roof can be
 *  lifted the moment somebody walks in without any per-scene script bookkeeping.
 *  `flat` marks a prop that is painted onto a wall rather than standing on the ground —
 *  a hanging scroll, a plaque. Nobody can stand behind it, so it never goes translucent. */
export type ArtObject = { name:string; asset:string; x:number; y:number; width:number; height:number; visibility:string; depthOffset:number; interiorZone?: string; flat?: boolean };
/** A raised stone platform. `court` is a terrace with a plinth face, `path` a low walkway
 *  joining two courts along the processional axis. */
export type Terrace = { col:number; row:number; width:number; height:number; kind:'court'|'path' };
export type MapData = {
  width: number; height: number; tilewidth: number; tileheight: number;
  anchors: Record<string, Point>; zones: Zone[]; blockers: Zone[];
  routes: Record<string, string[]>; walkable: Set<string>;
  art: ArtObject[];
  id:string; title:string; theme:string; labels:{text:string;point:Point}[];
  /** `water` lists the canal or pond rectangles (col,row,w,h in grid units) a river stage
   *  paints over the floor. A stage without it keeps the historic garden pond rectangle. */
  water: [number,number,number,number][];
  /** `terraces` are the stone platforms an otherworldly stage stands its props on. The
   *  dream/myth/ruins themes skip the estate paving, which without a platform leaves every
   *  screen, bed and censer floating on a blank wash — furniture with no floor to stand on. */
  terraces: Terrace[];
  /** `walls` are the courtyard enclosure lines, each `col1,row1,col2,row2` in grid units.
   *  A Chinese courtyard reads as a courtyard only when it is walled: without them the
   *  buildings stand on an open field and the stage looks like a car park. Gaps between
   *  segments are the gates. */
  walls: [number,number,number,number][];
  /** Flowerbeds are a per-courtyard planting, not an estate-wide ornament. A string
   *  property lists `col,row,w,h;…`; `false` turns them off (a canal, a lane of dust). */
  beds: [number,number,number,number][];
  /** `lights` are hanging lanterns, `col,row;…`. A 灯市 is a street of them: the painted
   *  booths are bamboo frames, and the market only reads as a market once the lanterns
   *  hang from them. Kept as positions rather than sprites because a lantern is four
   *  shapes and a glow — cheaper and more consistent than another 1024 px render. */
  lights: [number,number][];
  /** `dusk` lays a cool veil over the paving only: a night street is dark underfoot and
   *  warm at the lanterns, and sprites stay readable instead of being tinted flat. */
  dusk: boolean;
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
  // A stage may declare its own water rectangles as "col,row,w,h;col,row,w,h", its own
  // courtyard walls as "col1,row1,col2,row2;…" and its own flowerbeds; each falls back to
  // the historic estate look only when the property is absent.
  const rects = (name: string) => {
    const value = raw.properties?.find(p => p.name === name)?.value;
    if (value === false || value === 'false' || value === undefined) return [];
    return typeof value === 'string' && value.trim()
      ? value.split(';').map(part => part.split(',').map(Number) as [number,number,number,number])
      : [];
  };
  const water = rects('water');
  const walls = rects('walls');
  // `lights` is a bare list of hanging points: "col,row;col,row".
  const lightProp = raw.properties?.find(p => p.name === 'lights')?.value;
  const lights: [number,number][] = typeof lightProp === 'string' && lightProp.trim()
    ? lightProp.split(';').map(part => part.split(',').map(Number) as [number,number])
    : [];
  // `beds` absent keeps the seven historic Rongguo garden beds; an explicit list (even an
  // empty one) replaces them, so every courtyard plants its own.
  const bedProp = raw.properties?.find(p => p.name === 'flowerbeds')?.value;
  const beds: [number,number,number,number][] = bedProp === undefined
    ? [[6,24,3,6],[6,15,3,5],[27,16,3,6],[29,5,4,4],[15,10,2,3],[24,19,4,2],[6,6,5,4]]
    : rects('flowerbeds');
  // "col,row,w,h[,court|path]" per terrace. Absent for every estate stage, which already
  // gets its paving from PlanZones.
  const terraceProp = raw.properties?.find(p => p.name === 'terraces')?.value;
  const terraces: Terrace[] = typeof terraceProp === 'string' && terraceProp.trim()
    ? terraceProp.split(';').map(part => { const [col, row, width, height, kind] = part.split(',');
        return { col: Number(col), row: Number(row), width: Number(width), height: Number(height), kind: kind === 'path' ? 'path' as const : 'court' as const }; })
    : [];
  const map: MapData = { width: raw.width, height: raw.height, tilewidth: raw.tilewidth, tileheight: unit,
    anchors, zones: zones('PlanZones'), blockers: zones('PlanBlockers'), routes: {}, walkable: new Set(), art: [],id:String(raw.properties?.find(p=>p.name==='sceneId')?.value??'entry'),title:String(raw.properties?.find(p=>p.name==='title')?.value??'荣国府 · 贾母院'),theme:String(raw.properties?.find(p=>p.name==='theme')?.value??'garden'),labels:[],water,terraces,walls,beds,lights,dusk:raw.properties?.find(p=>p.name==='dusk')?.value===true };
  for(const o of raw.layers.find(l=>l.name==='Labels')?.objects??[])map.labels.push({text:o.name,point:{col:o.x/unit-.5,row:o.y/unit-.5}});
  for(const o of raw.layers.find(l=>l.name==='Art')?.objects??[]) {
    if(o.visible===false)continue;
    if(o.rotation || (o.gid??0)>0x0fffffff)throw new Error(`素材 ${o.name} 暂不支持旋转或 Tiled 翻转，请使用校准后的变体`);
    const prop=(name:string)=>o.properties?.find(p=>p.name===name)?.value;
    const asset=prop('asset');
    if(typeof asset!=='string' || o.width<=0 || o.height<=0)throw new Error(`素材 ${o.name} 缺少有效图像与尺寸`);
    map.art.push({name:o.name,asset,x:o.x-o.y,y:(o.x+o.y)/2,width:o.width,height:o.height,visibility:String(prop('visibility')??'always'),depthOffset:Number(prop('depthOffset')??0),interiorZone:typeof prop('interiorZone')==='string'?String(prop('interiorZone')):undefined,flat:prop('flat')===true});
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
/** Nearest walkable cell to `target` that nobody stands on. Two script anchors
 *  sometimes name the same floor tile, and two people cannot share one: the
 *  later arrival steps aside to the closest free tile instead. The search is a
 *  breadth-first ring over the four walking neighbours, so the pick is the
 *  shortest detour, and ties fall to the smaller row then column so the result
 *  is deterministic for both a watched walk and a skipped one. */
export function nearestFreeCell(map: MapData, target: Point, occupied: Set<string>): Point | null {
  if (!occupied.has(cellKey(target.col, target.row))) return target;
  const seen = new Set([cellKey(target.col, target.row)]);
  let ring: Point[] = [target];
  while (ring.length) {
    const next: Point[] = [];
    for (const point of ring) {
      for (const [dc, dr] of [[0,-1],[-1,0],[1,0],[0,1]] as const) {
        const candidate = {col: point.col+dc, row: point.row+dr}, key = cellKey(candidate.col, candidate.row);
        if (seen.has(key) || !map.walkable.has(key)) continue;
        if (!occupied.has(key)) return candidate;
        seen.add(key); next.push(candidate);
      }
    }
    ring = next;
  }
  return null;
}

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
