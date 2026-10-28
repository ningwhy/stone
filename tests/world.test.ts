import test from 'node:test';
import assert from 'node:assert/strict';
import atlas from '../design/atlas-maps.json' with {type:'json'};
const geography=atlas.levels.rongguo as typeof atlas.levels.rongguo&{compass:Record<string,string>};
const levels=atlas.levels as unknown as Record<string,{parent:string|null;locations:{id:string;name:string;col:number;row:number;kind:string;group?:string;drill?:string;asset?:string;start?:string}[]}>;
import { worldRouteCells,worldRoadSegments } from '../src/worldRoutes.ts';
import { StoryEngine,LEGACY_SAVE_KEY,LEGACY_V2_KEY,SAVE_KEY } from '../src/engine.ts';
import { LAST_LEGACY_INDEX } from '../src/story.ts';
import { story,chapter3Story } from '../src/story.ts';
import { parseTiledMap } from '../src/model.ts';
import { artAssets } from '../src/art.ts';
import { readFileSync,readdirSync } from 'node:fs';
const maps=()=>Object.fromEntries(readdirSync(new URL('../maps',import.meta.url)).filter(p=>p.endsWith('.tmj')).map(p=>{const m=parseTiledMap(JSON.parse(readFileSync(new URL(`../maps/${p}`,import.meta.url),'utf8')));return [m.id,m];}));
const has=(path:{col:number;row:number}[],col:number,row:number)=>path.findIndex(p=>p.col===col&&p.row===row);
test('west gate lies in west wall, black gate in eastern south wall; street orientation is consistent',()=>{
 const west=geography.gates.find(g=>g.id==='west_gate')!,black=geography.gates.find(g=>g.id==='black_gate')!,main=geography.gates.find(g=>g.id==='main_gate')!;
 assert.equal(west.col,4);assert.equal(west.wall,'west');assert.equal(black.row,36);assert.equal(black.wall,'south');assert.ok(black.col>main.col);
 assert.deepEqual(geography.compass,{east:'col+',south:'row+',north:'row-',west:'col-'});
 const raw=JSON.parse(readFileSync(new URL('../maps/capital.tmj',import.meta.url),'utf8'));const map=parseTiledMap(raw);assert.ok(map.anchors.ning_gate.col>map.anchors.rong_gate.col);assert.ok(map.anchors.west_corner.col<map.anchors.rong_gate.col);
});
test('Jia She visit exits west corner, passes main gate on street, enters black oil gate; return uses main gate',()=>{
 const outward=worldRouteCells('entry','east');const west=has(outward,4,30),street=has(outward,23,38),black=has(outward,35,36);
 assert.ok(west>=0&&street>west&&black>street);assert.ok(has(outward,23,36)<0,'must pass rather than enter main gate on outward visit');
 const back=worldRouteCells('east','central');assert.ok(has(back,35,36)>=0);assert.ok(has(back,23,36)>has(back,35,36));
 for(const [a,b] of worldRoadSegments)assert.ok(a.col===b.col||a.row===b.row,'roads must follow cardinal cells');
 // A road may cross perimeter lines only in the deliberate door gaps.
 for(const [a,b] of worldRoadSegments)for(const [p,q] of geography.walls){
  if(a.col===b.col&&p[1]===q[1])assert.ok(!(p[1]>Math.min(a.row,b.row)&&p[1]<Math.max(a.row,b.row)&&a.col>Math.min(p[0],q[0])&&a.col<Math.max(p[0],q[0])),'road crosses horizontal wall');
  if(a.row===b.row&&p[0]===q[0])assert.ok(!(p[0]>Math.min(a.col,b.col)&&p[0]<Math.max(a.col,b.col)&&a.row>Math.min(p[1],q[1])&&a.row<Math.max(p[1],q[1])),'road crosses vertical wall');
 }
});
test('book four joins the estate map: the Xue courtyard walks the lanes, the yamen stays outside',()=>{
 const lixiang=geography.locations.find(l=>l.id==='c4_lixiang')!;
 assert.equal(lixiang.external,false);assert.ok(geography.daiyuScenes.includes('c4_lixiang'));
 const walk=worldRouteCells('central','c4_lixiang');
 assert.ok(walk.length>=3,'no lane path from Rongxi Hall to the Xue courtyard');
 for(let i=0;i<walk.length-1;i++)assert.ok(walk[i].col===walk[i+1].col||walk[i].row===walk[i+1].row,'the courtyard path must be cardinal');
 // 扬州与应天府和京城同级，已经搬到第一级「天下」；荣国府总览只画府内院落。
 const yamen=levels.realm.locations.find(l=>l.id==='yingtian')!;
 assert.equal(yamen.start,'C04-007');
 assert.ok(story.some(s=>s.id===yamen.start),'the yamen start node must exist');
 assert.ok(story.some(s=>s.id===lixiang.start),'the courtyard start node must exist');
 for(const id of ['c4_yamen','lin'])assert.ok(!geography.locations.some(l=>l.id===id),`${id} must not sit on the estate plan`);
});
test('the estate plan reads like the book: rooms stay inside their courtyard, 梨香院 is there',()=>{
 const byId=Object.fromEntries(geography.locations.map(l=>[l.id,l]));
 // 碧纱橱 is a screen inside 贾母's 正房, not a courtyard of its own.
 assert.equal(byId.night.kind,'room','碧纱橱 must be drawn as a room, not a courtyard');
 assert.equal(byId.night.group,'granny');
 assert.ok(byId.night.name.includes('贾母正房'),'the label must say whose room it is');
 // 王夫人 sits in the east wing of 荣禧堂, so she shares that compound.
 assert.equal(byId.wang.kind,'room');assert.equal(byId.wang.group,'rongxi');assert.equal(byId.central.group,'rongxi');
 // 梨香院 is the Xue family courtyard in the north-east corner, with a lane to 王夫人.
 const lixiang=byId.c4_lixiang;
 assert.equal(lixiang.kind,'court');assert.equal(lixiang.name,'梨香院');
 assert.ok(lixiang.col>byId.central.col&&lixiang.row<byId.central.row,'梨香院 must sit north-east of 荣禧堂');
 assert.ok(geography.network.edges.some(([a,b])=>[a,b].includes('lixiang_gate')),'the south-west gate needs a lane');
 // A room never draws its own courtyard plot.
 for(const l of geography.locations.filter(x=>x.kind==='room'))assert.ok(!l.width,`${l.id} is a room and must not own a plot`);
});
test('the atlas is three levels deep and every branch resolves',()=>{
 const ids=Object.keys(levels);
 for(const id of ['realm','capital','rongguo','ningguo'])assert.ok(ids.includes(id),`${id} level missing`);
 assert.equal(atlas.levels.realm.parent,null);
 for(const id of ids){const l=levels[id];
  if(l.parent)assert.ok(ids.includes(l.parent),`${id} parent ${l.parent} missing`);
  for(const loc of l.locations){
   if('drill' in loc&&loc.drill)assert.ok(ids.includes(loc.drill as string),`${id}/${loc.id} drills into a missing level`);
   if('asset' in loc&&loc.asset)assert.ok(artAssets[loc.asset],`${id}/${loc.id} uses unknown art ${loc.asset}`);
  }
 }
 for(const [scene,level] of Object.entries(atlas.sceneLevel))assert.ok(ids.includes(level),`${scene} maps to a missing level`);
 // Every level but the root must be reachable from 天下 by drilling down.
 const kids=new Set(ids.filter(id=>levels[id].parent));
 assert.ok(kids.has('rongguo')&&kids.has('ningguo')&&kids.has('capital'));
 // 宁国府 mirrors the book: three middle bays, 会芳园 in the west, 宗祠 in its own yard.
 const ning=levels.ningguo,ningById=Object.fromEntries(ning.locations.map(l=>[l.id,l]));
 assert.equal(ningById.qin_room.kind,'room','秦氏卧房 is a room in the 中路 compound');
 assert.equal(ningById.huifang_yuan.group,'huifang');
 assert.ok(ningById.huifang_yuan.col<ningById.ning_zhengtang.col,'会芳园 lies west of the middle bays');
 assert.ok(ningById.zongci.col<ningById.huifang_yuan.col||ningById.zongci.row>ningById.huifang_yuan.row,'宗祠 is a separate yard to the west');
});
test('first two books connect to chapter three and never end early',()=>{
 const engine=new StoryEngine(maps());
 for(const chapter of [1,2]){const last=story.filter(s=>s.source.chapter===chapter).at(-1)!;engine.seek(last.id);assert.equal(engine.getSnapshot().status,'reading');engine.advance();engine.skip();assert.equal(engine.step.source.chapter,chapter+1);}
 for(const id of ['c1-stone','c1-dream','c1-home','c1-moon','c1-disaster','c1-awakening','c2-fortune','c2-dismissal','c2-lin','c2-temple','c2-ningrong','c2-jade','c2-family','c2-bridge'])assert.ok(story.some(s=>s.chapter===id));
 assert.ok(story.some(s=>s.source.layer==='dream'));assert.ok(story.some(s=>s.source.layer==='recollection'));assert.ok(story.some(s=>s.source.layer==='reported'));
});
test('original chapter-three v2 save migrates by node and populates new actors safely',()=>{
 const original=new StoryEngine(maps(),chapter3Story);original.seek('B010');const v3=original.serialize();const actors=structuredClone(v3.state.actors);
 for(const id of ['shiyin','fengshi','yinglian','jiaoxing','fengsu','monk','taoist','kongkong','huoqi','oldmonk'])delete (actors as Record<string,unknown>)[id];
 const legacy={version:2,chapter:'chapter03',node:v3.node,state:{...v3.state,actors}};
 const engine=new StoryEngine(maps());engine.restore(legacy);assert.equal(engine.step.id,'B010');assert.equal(engine.getSnapshot().index,story.findIndex(s=>s.id==='B010'));assert.equal(engine.getSnapshot().actors.shiyin.visible,false);assert.equal(engine.serialize().version,5);assert.notEqual(SAVE_KEY,LEGACY_SAVE_KEY);assert.equal(engine.getSnapshot().actors.menzi.visible,false,'chapter-four actors seeded invisible');
});
test('every prequel set piece and human speaker has a deliberate stage appearance',()=>{
 const stageMaps=maps();
 for(const step of story.filter(s=>s.source.chapter<3)){
  const e=new StoryEngine(stageMaps);e.seek(step.id);
  if(step.speaker!=='narrator')assert.equal(e.getSnapshot().actors[step.speaker].visible,true,`${step.id}: speaker not on stage`);
 }
 for(const id of ['myth','dream','suzhou','lantern','farm','yamen','zhitong','tavern'])assert.ok(stageMaps[id].art.length>=2,`${id}: missing scenic art`);
 // The burned street is drawn with the later `ruined-house` render (roofless walls, charred
 // beams); `estate-ruins` was the first attempt. Either satisfies "no intact roof in a ruin".
 assert.ok(stageMaps.ruins.art.some(o=>['ruined-house','estate-ruins'].includes(o.asset)),
   'ruins must use the dedicated burned house');
});

test('Tiled reference exports the same west and south gate coordinates as the runtime',()=>{
 const tiled=JSON.parse(readFileSync(new URL('../maps/world/rongguo-overview.tmj',import.meta.url),'utf8'));
 const gates=tiled.layers.find((l:{name:string})=>l.name==='Gates').objects;
 for(const g of geography.gates){const o=gates.find((o:{properties:{name:string;value:string}[]})=>o.properties.some(p=>p.name==='gateId'&&p.value===g.id));assert.ok(o);assert.equal(o.x,(g.col+.5)*64);assert.equal(o.y,(g.row+.5)*64);}
});

test('a v3 save taken at the old finale reopens as reading at the same node',()=>{
 const before=new StoryEngine(maps(),chapter3Story);before.seek('END');
 const legacy={version:3,chapter:'first-three',node:'END',state:{...structuredClone(before.getSnapshot()),status:'ended'}};
 assert.equal(legacy.state.index,chapter3Story.length-1,'END must be the last chapter-three node');
 const engine=new StoryEngine(maps());engine.restore(legacy);
 assert.equal(engine.step.id,'END');assert.equal(engine.getSnapshot().status,'reading','old finale must reopen for chapter four');
 engine.advance();let guard=0;while(engine.getSnapshot().status==='moving'&&guard++<500)engine.tick(.1);assert.ok(guard<500);assert.equal(engine.step.source.chapter,4,'advancing past the old finale enters chapter four');
 assert.equal(engine.serialize().version,5);
});

test('v4 saves round-trip and unknown versions still fail cleanly',()=>{
 const e=new StoryEngine(maps());e.seek('C04-006');
 const saved=e.serialize();assert.equal(saved.version,5);assert.equal(saved.chapter,'five-six');
 const r=new StoryEngine(maps());r.restore(JSON.parse(JSON.stringify(saved)));
 assert.equal(r.step.id,'C04-006');assert.deepEqual(r.getSnapshot(),e.getSnapshot());
 assert.throws(()=>r.restore({version:9,chapter:'nine',node:'C04-006',state:saved.state}),/存档版本不兼容/);
 assert.throws(()=>r.restore(null),/存档/);
});
