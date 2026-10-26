import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync,readdirSync } from 'node:fs';
import { StoryEngine } from '../src/engine.ts';
import { parseTiledMap, findPath, cellKey } from '../src/model.ts';
import { story,chapters } from '../src/story.ts';
const raw=JSON.parse(readFileSync(new URL('../maps/rongguo-entry.tmj',import.meta.url),'utf8'));
const maps=()=>Object.fromEntries(readdirSync(new URL('../maps',import.meta.url)).filter(p=>p.endsWith('.tmj')).map(p=>{const m=parseTiledMap(JSON.parse(readFileSync(new URL(`../maps/${p}`,import.meta.url),'utf8')));return [m.id,m];}));
const entry=()=>parseTiledMap(structuredClone(raw));
function settle(e:StoryEngine){let left=5000;while(e.getSnapshot().status==='moving'&&left-->0)e.tick(.1);assert.ok(left>0);assert.notEqual(e.getSnapshot().status,'error',e.getSnapshot().error??'');}
function normalize(e:StoryEngine){const s=structuredClone(e.getSnapshot());for(const a of Object.values(s.actors))a.direction=1;return s;}

test('entry A* takes a cardinal route around the explicit screen',()=>{const m=entry(),path=findPath(m,m.anchors.passage_entry,m.anchors.passage_exit);for(let i=0;i<path.length;i++){const p=path[i];assert.ok(m.walkable.has(cellKey(p.col,p.row)));assert.ok(!(p.col>=13&&p.col<15&&p.row===20));if(i)assert.equal(Math.abs(p.col-path[i-1].col)+Math.abs(p.row-path[i-1].row),1);}});
test('Tiled actual coordinates take precedence over custom properties',()=>{const edited=structuredClone(raw);edited.layers.find((l:{name:string})=>l.name==='Anchors').objects.find((o:{name:string})=>o.name==='daiyu_seat').x+=64;assert.deepEqual(parseTiledMap(edited).anchors.daiyu_seat,{col:21,row:6});});
test('all story nodes animate and skip to identical complete states across every map',()=>{const a=new StoryEngine(maps()),b=new StoryEngine(maps());const visited=new Set<string>();for(let i=0;i<story.length;i++){settle(a);b.skip();assert.deepEqual(normalize(a),normalize(b),a.step.id);visited.add(a.map.id);for(const actor of Object.values(a.getSnapshot().actors))if(actor.visible)assert.ok(a.map.walkable.has(cellKey(actor.col,actor.row)),`${a.step.id} invalid position`);if(i<story.length-1){a.advance();b.advance();}}assert.equal(a.getSnapshot().status,'ended');assert.equal(a.getSnapshot().history.length,story.length);assert.equal(visited.size,22);});
test('every chapter can be selected and saved/restored without missing scene state',()=>{for(const ch of chapters){const e=new StoryEngine(maps());e.seek(ch.start);assert.equal(e.step.id,ch.start);assert.equal(e.step.chapter,ch.id);const restored=new StoryEngine(maps());restored.restore(JSON.parse(JSON.stringify(e.serialize())));assert.deepEqual(restored.getSnapshot(),e.getSnapshot());restored.advance();settle(restored);}});
test('pause freezes walking and special actions; modal pause preserves manual pause',()=>{for(const node of ['N005','B022']){const e=new StoryEngine(maps());e.seek(node);e.advance();e.tick(.1);e.pause(true);const snapshot=structuredClone(e.getSnapshot());for(let n=0;n<30;n++)e.tick(.1);assert.deepEqual(e.getSnapshot(),snapshot);e.overlay(true);e.overlay(false);assert.equal(e.getSnapshot().paused,true);e.pause(false);settle(e);}});
test('rapid advance cannot cross an active move or duplicate history',()=>{const e=new StoryEngine(maps());e.seek('N005');e.advance();for(let i=0;i<50;i++)e.advance();assert.equal(e.step.id,'N006');settle(e);assert.equal(e.getSnapshot().history.filter(h=>h.id==='N006').length,1);});
test('invalid scene saves and in-flight saves fail without corrupting live state',()=>{const e=new StoryEngine(maps());e.seek('N005');e.advance();assert.throws(()=>e.serialize(),/移动结束/);e.skip();const original=structuredClone(e.getSnapshot());for(const input of [null,{}, {...e.serialize(),node:'bad'},{...e.serialize(),state:{...e.getSnapshot(),sceneId:'missing'}},{...e.serialize(),state:{...e.getSnapshot(),actors:{...e.getSnapshot().actors,daiyu:{col:0,row:0,visible:true,moving:false,direction:1}}}}]){assert.throws(()=>e.restore(input));assert.deepEqual(e.getSnapshot(),original);}});
test('errors identify node and missing route; restart clears scene, effects and jobs',()=>{const altered=structuredClone(story.filter(s=>s.source.chapter===3));altered[1].actions=[{type:'move',actor:'yucun',via:['missing']}];const e=new StoryEngine(maps(),altered);e.advance();assert.equal(e.getSnapshot().status,'error');assert.match(e.getSnapshot().error!,/P002.*missing/);e.restart();assert.equal(e.step.id,'P001');assert.equal(e.map.id,'lin');assert.equal(e.getSnapshot().effect,null);assert.deepEqual(e.getSnapshot().history.map(h=>h.id),['P001']);});
test('presentation gets a defensive copy of the actual remaining A* route',()=>{const e=new StoryEngine(maps());e.seek('N005');e.advance();const paths=e.movementPaths();const original=e.movementPaths()[0].points[1];paths[0].points[1].col=-100;assert.deepEqual(e.movementPaths()[0].points[1],original);e.skip();assert.deepEqual(e.movementPaths(),[]);});
test('source trace and chronology cover the chapter including the opening and final letter',()=>{assert.equal(new Set(story.map(s=>s.id)).size,story.length);for(const s of story){assert.ok([1,2,3,4].includes(s.source.chapter));assert.ok(s.source.paragraphLead);assert.ok(s.text);assert.ok(chapters.some(c=>c.id===s.chapter));}assert.equal(story[0].id,'C1-001');assert.equal(story.at(-1)?.id,'C04-112');assert.ok(story.some(s=>s.id==='END'));const e=new StoryEngine(maps());e.seek('F001');assert.equal(e.getSnapshot().actors.feng.visible,false);assert.equal(e.step.offscreen,true);e.seek('U014');assert.equal(e.getSnapshot().actors.zheng.visible,false);e.seek('D009');assert.equal(e.getSnapshot().actors.baoyu.visible,false);e.seek('B023');assert.equal(e.getSnapshot().effect,null);});

test('all cast members appear; Zhang Rugui and Leng Zixing are visible in their opening dialogue',()=>{
 const e=new StoryEngine(maps()),seen=new Set<string>();
 for(let i=0;i<story.length;i++){e.skip();for(const [id,a] of Object.entries(e.getSnapshot().actors))if(a.visible)seen.add(id);if(i<story.length-1)e.advance();}
 for(const id of Object.keys(e.getSnapshot().actors))assert.ok(seen.has(id),`${id} never appears`);
 for(const [node,id] of [['P002','zhang'],['P004','leng'],['N005','guide'],['N009','maid']] as const){e.seek(node);assert.equal(e.step.speaker,id);assert.equal(e.getSnapshot().actors[id].visible,true);}
});

test('the read log survives a jump backwards, so 回看 is the whole reading and not only the last stretch',()=>{
 const e=new StoryEngine(maps());
 e.seek('N005');
 for(let i=0;i<6;i++){e.skip();e.advance();}
 const read=e.readHistory();
 assert.ok(read.length>=6,`only ${read.length} lines were read`);
 const firstId=read[0].id;
 // Jump back to the very beginning of the chapter: the lines already read must not vanish.
 e.seek('P001');
 const after=e.readHistory();
 assert.ok(after.length>=read.length,`the log shrank from ${read.length} to ${after.length}`);
 assert.ok(after.some(entry=>entry.id===firstId),'the first line read is still in the log');
 // The log is ordered by the story, not by the order the reader happened to read in.
 const order=after.map(entry=>story.findIndex(s=>s.id===entry.id));
 assert.deepEqual(order,[...order].sort((a,b)=>a-b),'the log is out of order');
 // And the entries carry the text as it was read, not a bare id.
 for(const entry of after){assert.ok(entry.text.length>0);assert.ok(entry.speaker.length>0);}
});

test('a jump backwards keeps the log and the engine reports a reader freeze separately from a panel pause',()=>{
 const e=new StoryEngine(maps());
 e.seek('N005');e.skip();e.advance();
 const before=e.readHistory().length;
 e.seek('P001');
 assert.ok(e.readHistory().length>=before);
 // An open panel pauses the performance but is not the reader's freeze.
 e.overlay(true);
 assert.equal(e.getSnapshot().paused,true);
 assert.equal(e.stagePaused,false,'a panel pause must not look like a reader freeze');
 e.overlay(false);
 assert.equal(e.getSnapshot().paused,false);
 // The reader's own freeze does show as one, and clears only when the reader says so.
 e.pause(true);
 assert.equal(e.getSnapshot().paused,true);
 assert.equal(e.stagePaused,true);
 e.overlay(true);e.overlay(false);
 assert.equal(e.stagePaused,true,'an open panel must not clear the reader freeze');
 e.pause(false);
 assert.equal(e.getSnapshot().paused,false);
});

test('两个人不能共占一块地板：剧本把他们排进同一锚点时，后到者让到最近空格',()=>{
 const e=new StoryEngine(maps());
 for(let i=0;i<story.length;i++){
  settle(e);
  const byCell=new Map<string,string[]>();
  for(const [id,a] of Object.entries(e.getSnapshot().actors)){
   if(!a.visible)continue;
   const k=cellKey(a.col,a.row);
   if(!byCell.has(k))byCell.set(k,[]);
   byCell.get(k)!.push(id);
  }
  for(const [k,ids] of byCell)assert.equal(ids.length,1,`${e.step.id} stages ${ids.join(' + ')} on tile ${k}`);
  if(i<story.length-1)e.advance();
 }
});
