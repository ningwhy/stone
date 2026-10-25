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
if(errors.length){for(const error of errors)console.error(`ERROR ${error}`);process.exitCode=1;}
else console.log(`Content passed: ${story.length} nodes, ${chapters.length} sections, ${maps.size} maps, ${Object.keys(cast).length-1} humans, ${Object.keys(manifest).length} assets; chapter counts ${JSON.stringify(Object.fromEntries(books))}; ${docFiles.length} documentation files linked; ${evidenceEntries} evidence entries in ${evidenceFiles.length} table(s). Original-text interpretation and visuals still require human review.`);
