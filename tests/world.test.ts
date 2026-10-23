import test from 'node:test';
import assert from 'node:assert/strict';
import geography from '../design/rongguo-world.json' with {type:'json'};
import { worldRouteCells,worldRoadSegments } from '../src/worldRoutes.ts';
import { StoryEngine,LEGACY_SAVE_KEY,SAVE_KEY } from '../src/engine.ts';
import { story,chapter3Story } from '../src/story.ts';
import { parseTiledMap } from '../src/model.ts';
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
 const engine=new StoryEngine(maps());engine.restore(legacy);assert.equal(engine.step.id,'B010');assert.equal(engine.getSnapshot().index,story.findIndex(s=>s.id==='B010'));assert.equal(engine.getSnapshot().actors.shiyin.visible,false);assert.equal(engine.serialize().version,3);assert.notEqual(SAVE_KEY,LEGACY_SAVE_KEY);
});
test('every prequel set piece and human speaker has a deliberate stage appearance',()=>{
 const stageMaps=maps();
 for(const step of story.filter(s=>s.source.chapter<3)){
  const e=new StoryEngine(stageMaps);e.seek(step.id);
  if(step.speaker!=='narrator')assert.equal(e.getSnapshot().actors[step.speaker].visible,true,`${step.id}: speaker not on stage`);
 }
 for(const id of ['myth','dream','suzhou','lantern','farm','yamen','zhitong','tavern'])assert.ok(stageMaps[id].art.length>=2,`${id}: missing scenic art`);
 assert.ok(stageMaps.ruins.art.some(o=>o.asset==='estate-ruins'),'ruins must use the dedicated burned house');
});

test('Tiled reference exports the same west and south gate coordinates as the runtime',()=>{
 const tiled=JSON.parse(readFileSync(new URL('../maps/world/rongguo-overview.tmj',import.meta.url),'utf8'));
 const gates=tiled.layers.find((l:{name:string})=>l.name==='Gates').objects;
 for(const g of geography.gates){const o=gates.find((o:{properties:{name:string;value:string}[]})=>o.properties.some(p=>p.name==='gateId'&&p.value===g.id));assert.ok(o);assert.equal(o.x,(g.col+.5)*64);assert.equal(o.y,(g.row+.5)*64);}
});
