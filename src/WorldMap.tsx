import { useState, useEffect, useRef } from 'react';
import { artAssets, artImage } from './art.ts';
import { worldRouteCells, worldRoadSegments } from './worldRoutes.ts';
import geography from '../design/rongguo-world.json' with {type:'json'};

export const worldLocations=geography.locations;
export type Travel={from:string;to:string;progress:number};
const location=(id:string)=>worldLocations.find(l=>l.id===id)!;
export function worldLocationFor(scene:string,focus:string){return scene==='wang'&&['feng_room','back_lane'].includes(focus)?'feng':scene;}
function iso(col:number,row:number){return {x:720+(col-row)*17,y:55+(col+row)*8.5};}
const point=(id:string)=>{const l=location(id);return l?iso(l.col,l.row):iso(2,38);};
export function travelRoute(from:string,to:string):Omit<Travel,'progress'>|null {
  if(!geography.daiyuScenes.includes(from)||!geography.daiyuScenes.includes(to)||from===to)return null;
  return {from,to};
}
export function routePoints(from:string,to:string){return worldRouteCells(from,to).map(p=>iso(p.col,p.row));}
export function alongRoute(from:string,to:string,t:number){
  const points=routePoints(from,to),lengths=points.slice(1).map((p,i)=>Math.hypot(p.x-points[i].x,p.y-points[i].y));
  let distance=Math.max(0,Math.min(1,t))*lengths.reduce((a,b)=>a+b,0);
  for(let i=0;i<lengths.length;i++){if(distance<=lengths[i]&&lengths[i]>0){const f=distance/lengths[i];return {x:points[i].x+(points[i+1].x-points[i].x)*f,y:points[i].y+(points[i+1].y-points[i].y)*f};}distance-=lengths[i];}
  return points.at(-1)!;
}
export function WorldMap({sceneId,travel,onVisit}:{sceneId:string;travel:Travel|null;onVisit:(id:string)=>void}) {
  const [selected,setSelected]=useState<string|null>(null);
  const svg=useRef<SVGSVGElement>(null),[viewScale,setViewScale]=useState(1);
  useEffect(()=>{const node=svg.current;if(!node)return;const measure=()=>{const box=node.getBoundingClientRect();setViewScale(Math.min(box.width/1440,box.height/840));};const observer=new ResizeObserver(measure);observer.observe(node);measure();return ()=>observer.disconnect();},[]);
  const labelSize=Math.max(15,12/Math.max(.1,viewScale)),tokenHeight=Math.max(65,48/Math.max(.1,viewScale));
  const active=worldLocations.find(l=>l.id===(selected??sceneId));
  const token=travel?alongRoute(travel.from,travel.to,travel.progress):point(sceneId);
  const poly=(c:number,r:number,w:number,h:number)=>[[c,r],[c+w,r],[c+w,r+h],[c,r+h]].map(([x,y])=>{const p=iso(x,y);return `${p.x},${p.y}`;}).join(' ');
  const path=(points:{x:number;y:number}[])=>points.map(p=>`${p.x},${p.y}`).join(' ');
  const sites=worldLocations.filter(l=>!l.external).sort((a,b)=>a.col+a.row-b.col-b.row);
  const openSite=(id:string)=>setSelected(id);
  const imageAt=(asset:string,col:number,row:number,width:number,key:string)=>{const a=artAssets[asset],p=iso(col,row);if(!a)return null;const scale=width/a.width;return <image onLoad={e=>{e.currentTarget.dataset.loaded='true';}} key={key} href={a.image} x={p.x-a.anchor[0]*scale} y={p.y-a.anchor[1]*scale} width={width} height={a.height*scale} pointerEvents="none"/>;};
  const spine=geography.roads.spineCol;
  const roadLines=worldRoadSegments.map(segment=>path(segment.map(p=>iso(p.col,p.row))));
  return <div className="world-map" aria-label="荣国府总览">
    <div className="world-scroll"><svg ref={svg} viewBox="0 0 1440 840" role="img" aria-label="荣国府院落建筑、连廊与府内道路示意图">
      <defs>
        <pattern id="paper-grain" width="19" height="23" patternUnits="userSpaceOnUse"><circle cx="3" cy="7" r=".7" fill="#8f9777" opacity=".2"/><path d="m11 14 3 1" stroke="#8b9674" opacity=".12"/></pattern>
        <pattern id="paving" width="34" height="17" patternUnits="userSpaceOnUse"><path d="M0 8.5 17 0 34 8.5 17 17Z" fill="none" stroke="#bbb297" strokeWidth=".6" opacity=".45"/></pattern>
        <filter id="building-shadow"><feDropShadow dx="1" dy="7" stdDeviation="4" floodColor="#52614c" floodOpacity=".15"/></filter>
      </defs>
      <polygon points={poly(0,0,40,40)} fill="#bdc7a5" stroke="#94a17e" strokeWidth="2"/>
      <polygon points={poly(.8,.8,38.4,38.4)} fill="#dce0c9"/>
      <polygon points={poly(1,1,38,38)} fill="url(#paper-grain)"/>
      <polygon points={poly(2,1,14,34)} fill="#c8d2b6" opacity=".5"/>
      <polygon points={poly(23,2,15,34)} fill="#d3d6b9" opacity=".7"/>
      {geography.walls.map(([start,end],i)=>{const a=iso(start[0],start[1]),b=iso(end[0],end[1]);return <g key={i}><path d={`M${a.x},${a.y} ${b.x},${b.y} ${b.x},${b.y-17} ${a.x},${a.y-17}Z`} fill="#e9dfc6" stroke="#b8b493"/><path d={`M${a.x},${a.y-18} ${b.x},${b.y-18}`} stroke="#768674" strokeWidth="6"/></g>;})}
      {roadLines.map((p,i)=><g key={i}><polyline points={p} fill="none" stroke="#b9b398" strokeWidth="25"/><polyline points={p} fill="none" stroke="#eee4cd" strokeWidth="22"/><polyline points={p} fill="none" stroke="url(#paving)" strokeWidth="21"/></g>)}
      <text transform={`translate(${iso(spine,19).x-13},${iso(spine,19).y}) rotate(-26.565)`} fontSize="12" fill="#8b8e72">南 北 夹 道</text>
      {[[3,10],[3,18],[3,30],[14,32],[16,21],[24,5],[35,7],[36,18],[28,30],[16,4],[6,37],[33,22]].map(([c,r],i)=>imageAt('garden-tree',c,r,62,'tree'+i))}
      {[[5,12],[15,30],[35,10],[33,24]].map(([c,r],i)=>imageAt('garden-rock',c,r,48,'rock'+i))}
      {sites.map(l=>{const p=point(l.id),current=l.id===sceneId,a=artAssets[l.asset];const width=(l.width+l.height)*17*.86,scale=a?width/a.width:1;
        return <g key={l.id} onClick={()=>openSite(l.id)} className={`world-location ${current?'current':''}`} data-asset={l.asset}>
          <polygon points={poly(l.col-l.width/2,l.row-l.height/2,l.width,l.height)} fill={current?'#e4d7b4':'#ded6bf'} stroke={current?'#ab8650':'#b6b79a'} strokeWidth={current?2:1}/>
          <polygon points={poly(l.col-l.width/2+.3,l.row-l.height/2+.3,l.width-.6,l.height-.6)} fill="url(#paving)"/>
          {a&&<image onLoad={e=>{e.currentTarget.dataset.loaded='true';}} href={a.image} x={p.x-a.anchor[0]*scale} y={p.y-a.anchor[1]*scale} width={width} height={a.height*scale} filter="url(#building-shadow)"/>}

        </g>;
      })}
      <text x={iso(39,39).x+20} y={iso(39,39).y} fontSize={labelSize} fill="#6b795d">东 → 宁国府</text>
      {sites.map(l=>{const p=point(l.id),current=l.id===sceneId,labelWidth=Math.max(154,l.name.length*labelSize+18);return <g key={'label-'+l.id} role="button" tabIndex={0} aria-label={`查看${l.name}地点`} data-asset={l.asset} onClick={()=>openSite(l.id)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();openSite(l.id);}}}><g className="world-site-label" transform={`translate(${p.x},${p.y+19})`}><rect x={-labelWidth/2} y="0" width={labelWidth} height={labelSize+14} rx="5" fill={current?'#506b58':'#faf5e7'} stroke="#b8bda2"/><text y={labelSize+4} textAnchor="middle" fill={current?'#fff9e9':'#53664f'} fontSize={labelSize}>{l.name}</text></g></g>;})}
      {geography.gates.filter(g=>g.id!=='west_gate').map(g=><g key={g.id} data-gate={g.id}>{imageAt(g.asset,g.col,g.row,94,g.id)}<text x={iso(g.col,g.row).x} y={iso(g.col,g.row).y+(g.id==='main_gate'?43:25)} textAnchor="middle" fontSize={labelSize} fill="#506b58">{g.name}</text></g>)}
      <g className="world-context"><text x="100" y="630" fontSize="15" fill="#7a886e">府外行程</text>{worldLocations.filter(l=>l.external).map((l,i)=><g key={l.id} role="button" tabIndex={0} aria-label={`查看${l.name}地点`} onClick={()=>openSite(l.id)} onKeyDown={e=>{if(e.key==='Enter')openSite(l.id);}}><rect x="80" y={647+i*39} width="190" height="32" rx="5" fill="#f6f0df" stroke="#b6bea3"/><text x="175" y={669+i*39} textAnchor="middle" fontSize="14" fill="#5d735d">{l.name}</text></g>)}</g>
      <text x="860" y="730" fill="#92967b" fontSize="16" transform="rotate(-26.565,860,730)">宁 荣 街</text>
      {travel&&<polyline data-testid="world-travel-route" points={path(routePoints(travel.from,travel.to))} fill="none" stroke="#bd8c3b" strokeWidth="4" strokeDasharray="8 6"/>}
      {(geography.daiyuScenes.includes(sceneId)||travel)&&<g className="world-traveler" transform={`translate(${token.x} ${token.y})`} data-progress={travel?.progress??1}>
        <ellipse rx="19" ry="8" fill="#576e51" opacity=".25"/><image href={artImage('daiyu-chibi')} x={-tokenHeight*.35} y={-tokenHeight} width={tokenHeight*.7} height={tokenHeight}/><ellipse rx="21" ry="9" fill="none" stroke="#b38c47" strokeWidth="2"/>
      </g>}
      <g transform="translate(1200,100)"><path d="M0 38 48 14 30 39 0 38Z" fill="#7e8c71"/><text x="52" y="12" fill="#849174" fontSize="15">北</text></g>
    </svg></div>
    <div className="world-legend">院落、正屋与连廊 · 点击查看地点<span>北向右上 · 东向右下 · 西墙角门 / 南墙黑油门</span></div>
    {active&&selected&&<aside className="world-detail"><button className="world-detail-close" aria-label="关闭地点详情" onClick={()=>setSelected(null)}>×</button><strong>{active.name}</strong><p>{active.description}</p><button className="text-button" onClick={()=>onVisit(active.id)}>从此处剧情开始 →</button></aside>}
  </div>;
}
