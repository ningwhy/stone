import { story,bookNames } from './story.ts';
import { artAssets, assetImage } from './art.ts';
import stages from '../design/prequel-maps.json' with {type:'json'};
import stages4 from '../design/chapter04-maps.json' with {type:'json'};
const stageData={...stages,...stages4} as Record<string,{name:string;props:(string|number)[][]}>;
export function JourneyMap({chapter,sceneId,onVisit}:{chapter:number;sceneId:string;onVisit:(node:string)=>void}){
 const scenes=[...new Set(story.filter(s=>s.source.chapter===chapter).map(s=>s.scene))];
 return <div className="journey-map"><div className="journey-intro"><span>{bookNames[chapter]} · 行迹</span><p>按出场次序排列。梦境与现实分列，跨城行程不按距离比例绘制。</p></div><div className="journey-sites">{scenes.map((id,i)=>{const first=story.find(s=>s.source.chapter===chapter&&s.scene===id)!;const stage=stageData[id];const assetId=stage?.props.find(p=>String(p[0]).startsWith('estate-'))?.[0]??(id==='lin'?'river-boat':id==='dream'?'crimson-pearl':'spirit-stone');const art=artAssets[String(assetId)];return <button key={id} className={id===sceneId?'journey-site current':'journey-site'} onClick={()=>onVisit(first.id)}><span className="journey-number">{String(i+1).padStart(2,'0')}</span>{art&&<img src={assetImage(art)} alt=""/>}<strong>{stage?.name??first.place}</strong><small>{first.title}</small><span className="journey-enter">从此处开始 →</span></button>;})}</div></div>;
}
