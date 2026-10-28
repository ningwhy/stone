import { useMemo, useState, useEffect, useRef, useCallback } from 'react';
import { artAssets, artImage, assetImage } from './art.ts';
import { worldRouteCells } from './worldRoutes.ts';
import atlas from '../design/atlas-maps.json' with {type:'json'};

export type Travel={from:string;to:string;progress:number};
type Point={x:number;y:number};
type LevelDef={id:string;title:string;subtitle:string;parent:string|null;scale:number;origin:number[];
  legend?:string;note?:string;notice?:string;daiyuScenes?:string[];
  ground?:{rect:number[];tone:string;name:string}[];
  walls?:[number[],number[]][];
  gates?:{id:string;name:string;col:number;row:number;asset:string}[];
  groups?:{id:string;name:string;rect:number[];note?:string;quote?:string}[];
  locations:AnyPlace[];
  markers?:{name:string;col:number;row:number}[];
  labels?:[string,number,number][];
  network?:{nodes:Record<string,number[]>;edges:string[][];dreamEdges?:string[][]};};
type AnyPlace={id:string;name:string;col:number;row:number;width?:number;height?:number;kind:string;
  group?:string;asset:string;scene?:string;focus?:string;start?:string;external?:boolean;drill?:string;
  description:string;quote?:string;source?:string};

export const levels=atlas.levels as unknown as Record<string,LevelDef>;
export const sceneLevel=atlas.sceneLevel as Record<string,string>;
/** Every place on every level, flattened so callers can look a location up by its id. */
export const worldLocations=(Object.entries(levels).flatMap(([id,l])=>l.locations.map(p=>p)) as AnyPlace[]);
export function worldLocationFor(scene:string,focus:string){return scene==='wang'&&['feng_room','back_lane'].includes(focus)?'feng':scene;}
export function levelForScene(scene:string){return sceneLevel[scene]??null;}
/** The map is handed a place id (which is usually, but not always, the scene id — 凤姐院 is
 *  `feng`, its scene is `wang`), so resolve the level by the place first. */
export function levelForPlace(id:string){
  for(const [levelId,level] of Object.entries(levels))if(level.locations.some(p=>p.id===id))return levelId;
  return null;
}
export function atlasLevelFor(id:string){return levelForPlace(id)??levelForScene(id);}

function isoOf(level:LevelDef){const ox=level.origin[0],oy=level.origin[1],s=level.scale;
  return (col:number,row:number):Point=>({x:ox+(col-row)*s,y:oy+(col+row)*s/2});}

export function travelRoute(from:string,to:string):Omit<Travel,'progress'>|null {
  const scenes=levels.rongguo.daiyuScenes??[];
  if(!scenes.includes(from)||!scenes.includes(to)||from===to)return null;
  return {from,to};
}
export function routePoints(from:string,to:string){
  const iso=isoOf(levels.rongguo);
  return worldRouteCells(from,to).map(p=>iso(p.col,p.row));
}
export function alongRoute(from:string,to:string,t:number){
  const points=routePoints(from,to),lengths=points.slice(1).map((p,i)=>Math.hypot(p.x-points[i].x,p.y-points[i].y));
  let distance=Math.max(0,Math.min(1,t))*lengths.reduce((a,b)=>a+b,0);
  for(let i=0;i<lengths.length;i++){if(distance<=lengths[i]&&lengths[i]>0){const f=distance/lengths[i];return {x:points[i].x+(points[i+1].x-points[i].x)*f,y:points[i].y+(points[i+1].y-points[i].y)*f};}distance-=lengths[i];}
  return points.at(-1)!;
}

const CORNER=(c:number,r:number,w:number,h:number):[number,number][]=>[[c,r],[c+w,r],[c+w,r+h],[c,r+h]];

/** The smallest isometric box holding everything drawn on a level, so the first paint fills
 *  the panel instead of shrinking the estate into a corner of a 40x40 sheet. */
function contentBounds(level:LevelDef){
  const iso=isoOf(level);let x0=Infinity,y0=Infinity,x1=-Infinity,y1=-Infinity;
  const add=(p:Point)=>{x0=Math.min(x0,p.x);y0=Math.min(y0,p.y);x1=Math.max(x1,p.x);y1=Math.max(y1,p.y);};
  for(const [a,b] of level.walls??[]){add(iso(a[0],a[1]));add(iso(b[0],b[1]));}
  for(const l of level.locations){
    const w=(l.width??2),h=(l.height??2),s=l.kind==='room'?1:w;
    for(const [c,r] of CORNER(l.col-w/2,l.row-h/2,w,h))add(iso(c,r));
    void s;
  }
  for(const g of level.gates??[])add(iso(g.col,g.row));
  for(const m of level.markers??[])add(iso(m.col,m.row));
  for(const g of level.groups??[])for(const [c,r] of CORNER(g.rect[0],g.rect[1],g.rect[2],g.rect[3]))add(iso(c,r));
  if(!isFinite(x0))return {x0:0,y0:0,x1:1440,y1:840};
  const pad=80;
  return {x0:x0-pad,y0:y0-pad,x1:x1+pad,y1:y1+pad};
}

const TAB:Record<string,string>={realm:'天下舆图',capital:'京城总览',rongguo:'荣国府总览',ningguo:'宁国府总览',daguanyuan:'大观园'};
export const levelTabName=(id:string)=>TAB[id]??id;

export function WorldMap({sceneId,travel,onVisit}:{sceneId:string;travel:Travel|null;onVisit:(id:string)=>void}) {
  const [selected,setSelected]=useState<string|null>(null);
  const [level,setLevel]=useState<string>(()=>atlasLevelFor(sceneId)??'realm');
  const [zoom,setZoom]=useState(1),[pan,setPan]=useState<Point>({x:0,y:0});
  const svg=useRef<SVGSVGElement>(null),drag=useRef<{x:number;y:number;pan:Point}|null>(null);
  const [viewScale,setViewScale]=useState(1);
  // The reader jumps chapters from the toolbar; the atlas follows the story to the level that
  // holds the new place. It must not yank them back out of a branch they just drilled into,
  // so this only fires when the scene itself changes.
  const lastScene=useRef(sceneId);
  useEffect(()=>{
    if(lastScene.current===sceneId)return;
    lastScene.current=sceneId;
    const next=atlasLevelFor(sceneId);
    if(next)setLevel(next);
  },[sceneId]);
  useEffect(()=>{setZoom(1);setPan({x:0,y:0});},[level]);
  useEffect(()=>{const node=svg.current;if(!node)return;
    const measure=()=>{const box=node.getBoundingClientRect();setViewScale(Math.min(box.width/1440,box.height/840)||1);};
    const observer=new ResizeObserver(measure);observer.observe(node);measure();return ()=>observer.disconnect();},[]);

  const current=levels[level];
  const iso=useMemo(()=>isoOf(current),[current]);
  const bounds=useMemo(()=>contentBounds(current),[current]);
  const baseW=bounds.x1-bounds.x0,baseH=bounds.y1-bounds.y0;
  const vw=baseW/zoom,vh=baseH/zoom;
  const cx=(bounds.x0+bounds.x1)/2+pan.x,cy=(bounds.y0+bounds.y1)/2+pan.y;
  const setZoomAt=useCallback((next:number)=>{
    const clamped=Math.max(1,Math.min(4,Math.round(next*100)/100));
    setZoom(clamped);
    if(clamped<=1)setPan({x:0,y:0});
    else setPan(p=>({x:Math.max(-baseW/2,Math.min(baseW/2,p.x)),y:Math.max(-baseH/2,Math.min(baseH/2,p.y))}));
  },[baseW,baseH]);
  const onPointerDown=(e:React.PointerEvent)=>{if(zoom<=1)return;drag.current={x:e.clientX,y:e.clientY,pan};};
  const onPointerMove=(e:React.PointerEvent)=>{const d=drag.current;if(!d||!svg.current)return;
    const box=svg.current.getBoundingClientRect(),k=vw/Math.max(1,box.width);
    setPan({x:Math.max(-baseW/2,Math.min(baseW/2,d.pan.x-(e.clientX-d.x)*k)),y:Math.max(-baseH/2,Math.min(baseH/2,d.pan.y-(e.clientY-d.y)*k))});};
  const onPointerUp=()=>{drag.current=null;};

  const labelSize=Math.max(15,12/Math.max(.1,viewScale)),tokenHeight=Math.max(65,48/Math.max(.1,viewScale));
  const active=selected?worldLocations.find(l=>l.id===selected):worldLocations.find(l=>l.id===sceneId);
  const poly=(c:number,r:number,w:number,h:number)=>CORNER(c,r,w,h).map(([x,y])=>{const p=iso(x,y);return `${p.x},${p.y}`;}).join(' ');
  const path=(points:Point[])=>points.map(p=>`${p.x},${p.y}`).join(' ');
  const nodes=current.network?.nodes;
  const edgePoints=(a:string,b:string)=>[nodes![a],nodes![b]].map(([col,row])=>iso(col,row));
  const estate=levels.rongguo;
  const token=travel?alongRoute(travel.from,travel.to,travel.progress)
    :(nodes&&nodes[sceneId]?iso(nodes[sceneId][0],nodes[sceneId][1]):iso(20,20));
  const openSite=(id:string)=>setSelected(id);
  const imageAt=(asset:string,col:number,row:number,width:number,key:string)=>{
    const a=artAssets[asset],p=iso(col,row);if(!a)return null;const scale=width/a.width;
    return <image onLoad={e=>{e.currentTarget.dataset.loaded='true';}} key={key} href={assetImage(a)} x={p.x-a.anchor[0]*scale} y={p.y-a.anchor[1]*scale} width={width} height={a.height*scale} pointerEvents="none"/>;
  };
  const sites=[...current.locations].sort((a,b)=>a.col+a.row-b.col-b.row);
  const crumbs:string[]=[];for(let l:LevelDef|undefined=current;l;l=l.parent?levels[l.parent]:undefined)crumbs.unshift(l.id);
  const groupName=(id?:string)=>current.groups?.find(g=>g.id===id)?.name;

  return <div className="world-map" aria-label={`${current.title}总览`}>
    <div className="world-scroll">
      <svg ref={svg} viewBox={`${cx-vw/2} ${cy-vh/2} ${vw} ${vh}`} role="img" aria-label={`${current.title}院落与道路示意图`}
        onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={onPointerUp} onPointerLeave={onPointerUp}
        style={zoom>1?{cursor:'grab'}:undefined}>
        <defs>
          <pattern id="paper-grain" width="19" height="23" patternUnits="userSpaceOnUse"><circle cx="3" cy="7" r=".7" fill="#8f9777" opacity=".2"/><path d="m11 14 3 1" stroke="#8b9674" opacity=".12"/></pattern>
          <pattern id="paving" width="34" height="17" patternUnits="userSpaceOnUse"><path d="M0 8.5 17 0 34 8.5 17 17Z" fill="none" stroke="#bbb297" strokeWidth=".6" opacity=".45"/></pattern>
          <filter id="building-shadow"><feDropShadow dx="1" dy="7" stdDeviation="4" floodColor="#52614c" floodOpacity=".15"/></filter>
        </defs>
        <polygon points={`${bounds.x0},${bounds.y0} ${bounds.x1},${bounds.y0} ${bounds.x1},${bounds.y1} ${bounds.x0},${bounds.y1}`} fill="#bdc7a5" opacity=".3"/>
        {(current.ground??[]).map((g,i)=><polygon key={'ground'+i} points={poly(g.rect[0],g.rect[1],g.rect[2],g.rect[3])}
          fill={g.tone==='street'?'#dad4bc':g.tone==='garden'?'#c8d2b6':'#d3d6b9'} opacity={g.tone==='garden'?.55:.7}/>)}
        {(current.walls??[]).map(([start,end],i)=>{const a=iso(start[0],start[1]),b=iso(end[0],end[1]);const h=current.scale;
          return <g key={i}><path d={`M${a.x},${a.y} ${b.x},${b.y} ${b.x},${b.y-h} ${a.x},${a.y-h}Z`} fill="#e9dfc6" stroke="#b8b493"/><path d={`M${a.x},${a.y-h-1} ${b.x},${b.y-h-1}`} stroke="#768674" strokeWidth="6"/></g>;})}
        {nodes&&(current.network?.edges??[]).map(([a,b],i)=>{const p=edgePoints(a,b);
          return <g key={'road'+i}><polyline points={path(p)} fill="none" stroke="#b9b398" strokeWidth="25"/><polyline points={path(p)} fill="none" stroke="#eee4cd" strokeWidth="22"/><polyline points={path(p)} fill="none" stroke="url(#paving)" strokeWidth="21"/></g>;})}
        {nodes&&(current.network?.dreamEdges??[]).map(([a,b],i)=><polyline key={'dream'+i} points={path(edgePoints(a,b))} fill="none" stroke="#a9b3c6" strokeWidth="3" strokeDasharray="10 9"/>)}
        {(current.groups??[]).map(g=>{const [c,r,w,h]=g.rect,top=iso(c+w/2,r);
          return <g key={'group'+g.id} pointerEvents="none">
            <polygon points={poly(c,r,w,h)} fill="none" stroke="#8f9a7a" strokeWidth="2" strokeDasharray="9 7" opacity=".85"/>
            <text x={top.x} y={top.y-16} textAnchor="middle" fontSize="15" fill="#6b795d" letterSpacing="2">{g.name}</text>
          </g>;})}
        {sites.map(l=>{
          const p=iso(l.col,l.row),isCurrent=l.id===sceneId,a=artAssets[l.asset],isRoom=l.kind==='room';
          const w=l.width??4,h=l.height??4;
          const width=(w+h)*current.scale*.86,scale=a?width/a.width:1,shrink=isRoom?.72:1;
          return <g key={l.id} onClick={()=>openSite(l.id)} className={`world-location ${isCurrent?'current':''}`} data-asset={l.asset} data-kind={l.kind}>
            {!isRoom&&<polygon points={poly(l.col-w/2,l.row-h/2,w,h)} fill={isCurrent?'#e4d7b4':'#ded6bf'} stroke={isCurrent?'#ab8650':'#b6b79a'} strokeWidth={isCurrent?2:1}/>}
            {!isRoom&&<polygon points={poly(l.col-w/2+.3,l.row-h/2+.3,w-.6,h-.6)} fill="url(#paving)"/>}
            {isRoom&&<ellipse cx={p.x} cy={p.y} rx={width*.4} ry={width*.2} fill="#e6dcc2" stroke="#b0b295" strokeDasharray="4 3"/>}
            {a&&<image onLoad={e=>{e.currentTarget.dataset.loaded='true';}} href={assetImage(a)} x={p.x-a.anchor[0]*scale*shrink} y={p.y-a.anchor[1]*scale*shrink} width={width*shrink} height={a.height*scale*shrink} filter="url(#building-shadow)"/>}
          </g>;
        })}
        {(current.markers??[]).map((m,i)=>{const p=iso(m.col,m.row);
          return <g key={'marker'+i} pointerEvents="none"><circle cx={p.x} cy={p.y} r="3" fill="#98a189"/><text x={p.x+8} y={p.y+4} fontSize="12" fill="#7d8a70">{m.name}</text></g>;})}
        {(current.labels??[]).map(([text,col,row],i)=>{const p=iso(col,row);
          return <text key={'label'+i} x={p.x} y={p.y} fontSize="13" fill="#8b8e72" textAnchor="middle">{text}</text>;})}
        {sites.map(l=>{const p=iso(l.col,l.row),isCurrent=l.id===sceneId,isRoom=l.kind==='room';
          const labelWidth=Math.max(154,l.name.length*labelSize+18);
          return <g key={'label-'+l.id} role="button" tabIndex={0} aria-label={`查看${l.name}地点`} data-asset={l.asset} data-kind={l.kind} onClick={()=>openSite(l.id)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();openSite(l.id);}}}>
            <g className="world-site-label" transform={`translate(${p.x},${p.y+(isRoom?12:19)})`}>
              <rect x={-labelWidth/2} y="0" width={labelWidth} height={labelSize+(isRoom?26:14)} rx="5" fill={isCurrent?'#506b58':'#faf5e7'} stroke="#b8bda2"/>
              <text y={labelSize+4} textAnchor="middle" fill={isCurrent?'#fff9e9':'#53664f'} fontSize={labelSize}>{l.name}</text>
              {isRoom&&<text y={labelSize+23} textAnchor="middle" fill={isCurrent?'#e7efdf':'#93a086'} fontSize={labelSize-4}>房内空间 · 不另成一院</text>}
            </g></g>;})}
        {(current.gates??[]).map(g=>{const p=iso(g.col,g.row);
          return <g key={g.id} data-gate={g.id}>{imageAt(g.asset,g.col,g.row,current.scale*94/17,g.id)}
            <text x={p.x} y={p.y+34} textAnchor="middle" fontSize={labelSize} fill="#506b58">{g.name}</text></g>;})}
        {travel&&level==='rongguo'&&<polyline data-testid="world-travel-route" points={path(routePoints(travel.from,travel.to))} fill="none" stroke="#bd8c3b" strokeWidth="4" strokeDasharray="8 6"/>}
        {level==='rongguo'&&((estate.daiyuScenes??[]).includes(sceneId)||travel)&&<g className="world-traveler" transform={`translate(${token.x} ${token.y})`} data-progress={travel?.progress??1}>
          <ellipse rx="19" ry="8" fill="#576e51" opacity=".25"/><image href={artImage('daiyu-chibi')} x={-tokenHeight*.35} y={-tokenHeight} width={tokenHeight*.7} height={tokenHeight}/><ellipse rx="21" ry="9" fill="none" stroke="#b38c47" strokeWidth="2"/>
        </g>}
        <g transform={`translate(${bounds.x1-120},${bounds.y0+40})`}><path d="M0 38 48 14 30 39 0 38Z" fill="#7e8c71"/><text x="52" y="12" fill="#849174" fontSize="15">北</text></g>
      </svg>
    </div>
    <div className="world-crumbs" role="navigation" aria-label="舆图层级">
      {crumbs.map((id,i)=><span key={id}>{i>0&&<i aria-hidden="true">›</i>}<button onClick={()=>setLevel(id)} aria-current={i===crumbs.length-1}>{TAB[id]??id}</button></span>)}
    </div>
    <div className="world-zoom" role="group" aria-label="舆图缩放">
      <button aria-label="放大舆图" onClick={()=>setZoomAt(zoom*1.35)}>＋</button>
      <button aria-label="缩小舆图" onClick={()=>setZoomAt(zoom/1.35)}>−</button>
      <button aria-label="复位舆图" onClick={()=>{setZoom(1);setPan({x:0,y:0});}}>复位</button>
      <span>{Math.round(zoom*100)}%</span>
    </div>
    <div className="world-legend">{current.subtitle}<span>{current.legend??'北向右上 · 东向右下'}</span></div>
    {active&&selected&&<aside className="world-detail">
      <button className="world-detail-close" aria-label="关闭地点详情" onClick={()=>setSelected(null)}>×</button>
      <strong>{active.name}</strong>
      {groupName(active.group)&&<em className="world-detail-group">{groupName(active.group)}</em>}
      <p>{active.description}</p>
      {active.quote&&<blockquote className="world-detail-quote">{active.quote}</blockquote>}
      {active.source==='改编'&&<small className="world-detail-note">原文未写黛玉到此，此处为支线改编。</small>}
      {active.drill&&<button className="text-button" onClick={()=>{setSelected(null);setLevel(active.drill!);}}>进入{TAB[active.drill!]} →</button>}
      {active.scene&&<button className="text-button" onClick={()=>{setSelected(null);onVisit(active.id);}}>从此处剧情开始 →</button>}
    </aside>}
    {current.notice&&<aside className="world-notice">{current.notice}</aside>}
  </div>;
}
