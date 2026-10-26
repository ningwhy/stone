/** Read-only validation of registered story data, map references and production docs. */
import {readFileSync,existsSync,readdirSync} from 'node:fs';
import {resolve,dirname,relative} from 'node:path';
import {fileURLToPath} from 'node:url';
import {story,chapters,cast,bookNames} from '../src/story.ts';
import {parseTiledMap} from '../src/model.ts';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const read=path=>JSON.parse(readFileSync(resolve(root,path),'utf8'));
const errors=[],warnings=[];
const requireThat=(condition,message)=>{if(!condition)errors.push(message);};
const manifest=read('public/assets/rongguo/manifest.json').assets;
const maps=new Map();
for(const file of readdirSync(resolve(root,'maps')).filter(f=>f.endsWith('.tmj'))){
 try{const map=parseTiledMap(read(`maps/${file}`));requireThat(!maps.has(map.id),`Duplicate sceneId: ${map.id}`);maps.set(map.id,map);}
 catch(e){errors.push(`maps/${file}: ${e.message}`);}
}
for(const [key,asset] of Object.entries(manifest)){
 requireThat(existsSync(resolve(root,'public'+asset.image)),`${key}: missing runtime PNG`);
 requireThat(asset.width>0&&asset.height>0&&asset.anchor?.length===2&&asset.anchor.every(Number.isFinite),`${key}: invalid calibrated geometry`);
}
// A bitmap on disk that the manifest does not list is unreachable: the
// runtime looks every asset up by key. A full rebuild of the calibrated
// assets once dropped the portrait emotion variants this way, and every
// variant silently fell back to the neutral portrait.
const assetDir=resolve(root,'public/assets/rongguo');
for(const file of readdirSync(assetDir)){
 if(!file.endsWith('.png'))continue;
 const key=file.replace(/\.png$/,'');
 requireThat(!!manifest[key],`${key}: PNG on disk is not registered in the manifest`);
}
for(const map of maps.values())for(const art of map.art)requireThat(!!manifest[art.asset],`${map.id}: missing art ${art.asset}`);
const ids=new Set(),sections=new Map();
for(const section of chapters){
 requireThat(!sections.has(section.id),`Duplicate section ${section.id}`);sections.set(section.id,section);
 const first=story.find(s=>s.id===section.start);
 requireThat(!!first,`${section.id}: unknown start ${section.start}`);
 if(first){requireThat(first.chapter===section.id,`${section.id}: start belongs to another section`);requireThat(first.scene===section.scene,`${section.id}: start scene mismatch`);requireThat(first.source.chapter===section.book,`${section.id}: book mismatch`);}
}
function actionCheck(action,map,node){
 if(!action||typeof action!=='object'){errors.push(`${node}: malformed action`);return;}
 requireThat(['show','hide','move','parallel','roof','effect'].includes(action.type),`${node}: unsupported action ${action.type}`);
 if(action.type==='parallel'){
  requireThat(Array.isArray(action.moves)&&action.moves.length>0,`${node}: empty parallel moves`);
  const moves=action.moves??[];requireThat(new Set(moves.map(m=>m.actor)).size===moves.length,`${node}: duplicate simultaneous actor`);
  for(const move of moves){requireThat(move.type==='move',`${node}: parallel only supports move`);actionCheck(move,map,node);}return;
 }
 if(['show','hide','move','effect'].includes(action.type))requireThat(!!cast[action.actor],`${node}: unknown actor ${action.actor}`);
 if(action.type==='show')requireThat(!!map?.anchors[action.at],`${node}: unknown show anchor ${action.at}`);
 if(action.type==='move'){
  requireThat(Array.isArray(action.via)&&action.via.length>0,`${node}: empty movement`);
  for(const anchor of action.via??[])requireThat(!!map?.anchors[anchor],`${node}: unknown movement anchor ${anchor}`);
 }
 if(action.type==='effect')requireThat(['jade','greet','rest'].includes(action.kind)&&Number.isFinite(action.duration)&&action.duration>0,`${node}: unsupported effect`);
 if(action.type==='roof')requireThat(typeof action.visible==='boolean',`${node}: roof.visible must be boolean`);
}
const books=new Map();
for(const step of story){
 requireThat(!ids.has(step.id),`Duplicate story node ${step.id}`);ids.add(step.id);
 requireThat(typeof step.text==='string'&&step.text.trim().length>0,`${step.id}: empty text`);
 requireThat(step.speaker==='narrator'||!!cast[step.speaker],`${step.id}: unknown speaker ${step.speaker}`);
 const section=sections.get(step.chapter),map=maps.get(step.scene);
 requireThat(!!section,`${step.id}: unknown section ${step.chapter}`);requireThat(!!map,`${step.id}: unknown scene ${step.scene}`);
 requireThat(!!map?.anchors[step.focus],`${step.id}: unknown focus ${step.focus}`);
 requireThat(Number.isInteger(step.source?.chapter)&&!!bookNames[step.source.chapter],`${step.id}: missing book name`);
 requireThat(typeof step.source?.paragraphLead==='string'&&step.source.paragraphLead.trim().length>0,`${step.id}: missing source paragraph lead`);
 requireThat(typeof step.source?.textKind==='string'&&step.source.textKind.length>0,`${step.id}: missing text kind`);
 requireThat(!step.source?.layer||['present','dream','recollection','reported'].includes(step.source.layer),`${step.id}: invalid narrative layer`);
 if(section)requireThat(section.book===step.source?.chapter,`${step.id}: section/source book mismatch`);
 if(Array.isArray(step.actions))for(const action of step.actions)actionCheck(action,map,step.id);else errors.push(`${step.id}: actions must be array`);
 const book=step.source?.chapter;books.set(book,(books.get(book)??0)+1);
}
for(const actor of Object.keys(cast).filter(id=>id!=='sedan'))for(const kind of ['portrait','chibi'])requireThat(!!manifest[`${actor}-${kind}`],`${actor}: missing ${kind}`);
// The facing table decides whether a sprite is mirrored, so every painted
// head has to be in it. A bitmap that is not listed would be mirrored by
// accident or not at all.
const facingTable=read('design/character-facing.json');
const facingKeys=new Set([
 ...Object.entries(facingTable.actors??{}).flatMap(([actor,entry])=>['portrait','chibi'].map(kind=>`${actor}-${kind}`)),
 ...Object.keys(facingTable.variants??{}),
]);
for(const key of Object.keys(manifest)){
 if(!key.endsWith('-portrait')&&!key.endsWith('-chibi')&&!/-portrait-/.test(key))continue;
 requireThat(facingKeys.has(key),`${key}: no facing recorded, the sprite would be mirrored by accident`);
}
const sourceCode=readFileSync(resolve(root,'src/story.ts'),'utf8');
for(const book of books.keys()){
 const number=String(book).padStart(2,'0');
 for(const kind of ['story','sections'])requireThat(sourceCode.includes(`chapter${number}-${kind}.json`),`Chapter ${book}: missing explicit ${kind} import`);
 requireThat(existsSync(resolve(root,`docs/chapter${number}-source.txt`)),`Chapter ${book}: missing local source text`);
}
for(const file of readdirSync(resolve(root,'design')).filter(f=>/^chapter\d+-story\.json$/.test(f)))if(!sourceCode.includes(file))warnings.push(`Unregistered chapter draft: design/${file}`);
// Evidence table: every node needs a source entry whose lead is locatable in the
// archived base text, otherwise the "original text" claim cannot be checked.
const evidenceFiles=readdirSync(resolve(root,'design')).filter(f=>/^chapter\d+-evidence\.json$/.test(f));
const coveredNodes=new Set();
let evidenceEntries=0;
for(const file of evidenceFiles){
  const book=Number(file.match(/chapter(\d+)-/)[1]);
  const table=read(`design/${file}`);
  const sourcePath=resolve(root,`docs/chapter${String(book).padStart(2,'0')}-source.txt`);
  const baseText=existsSync(sourcePath)?readFileSync(sourcePath,'utf8'):'';
  const strip=text=>text.replace(/[\s，。、；：？！」』“”‘’「」『』（）()…—·《》〈〉\-]/g,'');
  const strippedBase=strip(baseText);
  for(const item of table.evidence??[]){
    evidenceEntries++;
    requireThat(!!item.id,`${file}: evidence entry without id`);
    requireThat(['explicit','design'].includes(item.classification),`${file}/${item.id}: invalid classification ${item.classification}`);
    requireThat(typeof item.paragraphLead==='string'&&item.paragraphLead.trim().length>0,`${file}/${item.id}: missing paragraph lead`);
    requireThat(['present','reported','recollection','dream'].includes(item.narrativeLayer),`${file}/${item.id}: invalid narrative layer ${item.narrativeLayer}`);
    requireThat(Array.isArray(item.appliesTo)&&item.appliesTo.length>0,`${file}/${item.id}: empty appliesTo`);
    if(item.classification==='explicit'){
      requireThat(!!item.excerpt,`${file}/${item.id}: explicit evidence without excerpt`);
      requireThat(strippedBase.includes(strip(item.paragraphLead)),`${file}/${item.id}: paragraph lead not found in the base text`);
      for(const node of item.appliesTo)coveredNodes.add(node);
    }else{
      requireThat(!!item.designDecision,`${file}/${item.id}: design entry without designDecision`);
      requireThat(!!item.uncertainty,`${file}/${item.id}: design entry without uncertainty`);
    }
  }
}
for(const step of story){
  const book=String(step.source?.chapter).padStart(2,'0');
  if(!evidenceFiles.includes(`chapter${book}-evidence.json`))continue;
  requireThat(coveredNodes.has(step.id),`${step.id}: no explicit evidence entry`);
}
// Validate only the maintained entry and production manual, not archived planning documents.
const docFiles=['README.md','AGENTS.md'];
function walk(path){for(const entry of readdirSync(path,{withFileTypes:true})){const child=resolve(path,entry.name);if(entry.isDirectory())walk(child);else if(entry.name.endsWith('.md'))docFiles.push(relative(root,child));}}
walk(resolve(root,'docs/production'));
for(const file of docFiles){
 const contents=readFileSync(resolve(root,file),'utf8');
 for(const match of contents.matchAll(/!?\[[^\]]*\]\(([^)]+)\)/g)){
  const target=match[1].replace(/^<|>$/g,'').split('#')[0];
  if(!target||/^[a-z][a-z0-9+.-]*:/i.test(target))continue;
  requireThat(existsSync(resolve(dirname(resolve(root,file)),decodeURIComponent(target))),`${file}: broken link ${target}`);
 }
}
for(const warning of warnings)console.warn(`WARN ${warning}`);
// The facing list is generated from the authoritative table; keep them in step.
{
 const listPath=resolve(root,'docs/production/facing-list.md');
 requireThat(existsSync(listPath),'docs/production/facing-list.md: missing; run scripts/build_facing_doc.py');
 const {spawnSync}=await import('node:child_process');
 const check=spawnSync('python3',[resolve(root,'scripts/build_facing_doc.py'),'--check'],{encoding:'utf8'});
 requireThat(check.status===0,`facing-list.md is out of date with design/character-facing.json: ${(check.stdout||'').trim()||(check.stderr||'').trim()}`);
}
// The soundtrack: every file the engine asks for must exist, and the theme table in
// src/audio.ts may only name pieces that were actually built. A piece that fails to
// decode would leave a stage silent with nothing in the build to say so.
{
 const audioDir=resolve(root,'public/assets/audio');
 const shipped=new Set(readdirSync(audioDir).filter(f=>f.endsWith('.ogg')).map(f=>f.replace(/\.ogg$/,'')));
 const engine=readFileSync(resolve(root,'src/audio.ts'),'utf8');
 const wanted=new Set([...engine.matchAll(/'(bgm-[a-z]+|sfx-[a-z-]+)'/g)].map(m=>m[1]));
 const missing=[...wanted].filter(name=>!shipped.has(name));
 requireThat(missing.length===0,`audio: ${missing.join(', ')} referenced by src/audio.ts but not built; run npm run art:audio`);
 const unused=[...shipped].filter(name=>!wanted.has(name));
 for(const name of unused)warnings.push(`audio: ${name}.ogg is built but not referenced by the engine`);
 // the engine must keep a piece for every theme a map actually declares. Tiled stores
 // map properties as {"name":"theme","value":"garden"} objects, so read them from JSON
 // rather than pattern-matching the file.
 const themes=new Set(readdirSync(resolve(root,'maps')).filter(f=>f.endsWith('.tmj'))
   .flatMap(f=>{const map=JSON.parse(readFileSync(resolve(root,'maps',f),'utf8'));
     return (map.properties??[]).filter(p=>p.name==='theme'&&typeof p.value==='string').map(p=>p.value);}));
 const table=engine.slice(engine.indexOf('BGM_BY_THEME'),engine.indexOf('};',engine.indexOf('BGM_BY_THEME')));
 const mapped=new Set([...table.matchAll(/^\s*([a-z]+):\s*'/gm)].map(m=>m[1]));
 const unmapped=[...themes].filter(t=>!mapped.has(t));
 requireThat(unmapped.length===0,`audio: map themes with no piece: ${unmapped.join(', ')} (they fall back to the garden piece)`);
}
// The runtime requests WebP exclusively (src/art.ts), so a PNG rebuilt without its
// WebP sibling ships the old bitmap forever — the sedan grew four bearers and the
// page kept showing the empty chair. Three gates: the sibling must exist, it must
// be at least as fresh as its PNG, and every manifest entry needs a version (the
// WebP content hash, or an identity revision) so a rebuilt asset gets a new URL.
{
 const {statSync}=await import('node:fs');
 const dir=resolve(root,'public/assets/rongguo');
 for(const file of readdirSync(dir).filter(f=>f.endsWith('.png'))){
  const webp=resolve(dir,file.replace(/\.png$/,'.webp'));
  if(!existsSync(webp)){errors.push(`${file}: no WebP sibling; run npm run art:webp`);continue;}
  if(statSync(webp).mtimeMs<statSync(resolve(dir,file)).mtimeMs)
   errors.push(`${file}: WebP sibling is older than the PNG; run npm run art:webp`);
 }
 const unversioned=Object.entries(manifest)
  .filter(([,a])=>!a.hash&&!a.identity?.revision).map(([k])=>k);
 requireThat(unversioned.length===0,
  `manifest entries with no cache version (no hash, no identity revision): ${unversioned.join(', ')}; run npm run art:webp`);
}
// 收集卡片：先 WARN 后 FAIL（设计稿 collection.md 第七节）——第一期只提示数据
// 漂移（引用了不存在的节点/场景、重复 id），不作为硬失败阻断上线。
{
 const cardData=read('design/collection-cards.json');
 const nodeIds=new Set(story.map(s=>s.id));
 const seen=new Set();
 for(const card of cardData.cards){
  if(seen.has(card.id))warnings.push(`collection: duplicate card id ${card.id}`);seen.add(card.id);
  if(!['place','line','token','bond'].includes(card.kind))warnings.push(`collection: ${card.id} has unknown kind ${card.kind}`);
  const scene=card.unlock.type==='read_scene'?card.unlock.scene:null;
  if(scene&&!maps.has(scene))warnings.push(`collection: ${card.id} references unknown scene ${scene}`);
  if(card.unlock.type==='read'&&!nodeIds.has(card.unlock.node))warnings.push(`collection: ${card.id} references unknown node ${card.unlock.node}`);
  // 归属卡必须指向真实存在的人物，且写明归属的方向；不能凭名字造人。
  if(card.kind==='bond'){
   if(!card.bond)warnings.push(`collection: ${card.id} has no bond relation`);
   else{
    if(!['granted','sold','taken'].includes(card.bond.mode))warnings.push(`collection: ${card.id} has unknown bond mode ${card.bond.mode}`);
    if(!card.bond.from||!card.bond.to)warnings.push(`collection: ${card.id} has an incomplete bond relation`);
   }
   if(card.actor&&!cast[card.actor])warnings.push(`collection: ${card.id} references unknown actor ${card.actor}`);
  }
  // 信物卡与归属卡声称的原文依据必须逐字出现在底本里。信物是「原文写明交到手上」
  // 的东西，归属是「原文写明这个人归了谁」——一旦引文与底本脱节，卡面就在替原文
  // 说话，这正是最不能悄悄腐烂的地方。
  if((card.kind==='token'||card.kind==='bond')&&card.source){
   const chapter=String(card.book).padStart(2,'0');
   const file=resolve(root,`docs/chapter${chapter}-source.txt`);
   if(!existsSync(file))warnings.push(`collection: ${card.id} has no source text for chapter ${card.book}`);
   else{
    const text=readFileSync(file,'utf8').replace(/\s+/g,'');
    const claim=card.source.replace(/\s+/g,'');
    if(!text.includes(claim))warnings.push(`collection: ${card.id} quotes text not found in docs/chapter${chapter}-source.txt`);
   }
  }
 }
}
// 流转账簿：与卡片同一门禁原则——先 WARN 后 FAIL。账面是最不能悄悄腐烂的：
// 引文必须逐字对底本，转手双方不能是空名，节点必须真实存在。
{
 const nodeIds=new Set(story.map(s=>s.id));
 const seen=new Set();
 for(const entry of read('design/ledger.json').entries){
  if(seen.has(entry.id))warnings.push(`ledger: duplicate entry id ${entry.id}`);seen.add(entry.id);
  if(!['granted','sold','taken','paid'].includes(entry.mode))warnings.push(`ledger: ${entry.id} has unknown mode ${entry.mode}`);
  if(!['money','clothing','item','person','favor'].includes(entry.category))warnings.push(`ledger: ${entry.id} has unknown category ${entry.category}`);
  if(!entry.from||!entry.to)warnings.push(`ledger: ${entry.id} has an incomplete transfer`);
  if(!nodeIds.has(entry.node))warnings.push(`ledger: ${entry.id} references unknown node ${entry.node}`);
  if(entry.amount!=null&&(typeof entry.amount!=='number'||!Number.isFinite(entry.amount)||entry.amount<=0))warnings.push(`ledger: ${entry.id} has an invalid amount ${entry.amount}`);
  if(entry.source){
   const chapter=String(entry.book).padStart(2,'0');
   const file=resolve(root,`docs/chapter${chapter}-source.txt`);
   if(!existsSync(file))warnings.push(`ledger: ${entry.id} has no source text for chapter ${entry.book}`);
   else{
    const text=readFileSync(file,'utf8').replace(/\s+/g,'');
    const claim=entry.source.replace(/\s+/g,'');
    if(!text.includes(claim))warnings.push(`ledger: ${entry.id} quotes text not found in docs/chapter${chapter}-source.txt`);
   }
  }
 }
}
if(errors.length){for(const error of errors)console.error(`ERROR ${error}`);process.exitCode=1;}
else console.log(`Content passed: ${story.length} nodes, ${chapters.length} sections, ${maps.size} maps, ${Object.keys(cast).length-1} humans, ${Object.keys(manifest).length} assets; chapter counts ${JSON.stringify(Object.fromEntries(books))}; ${docFiles.length} documentation files linked; ${evidenceEntries} evidence entries in ${evidenceFiles.length} table(s). Original-text interpretation and visuals still require human review.`);
