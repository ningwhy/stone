import { story,bookNames } from './story.ts';
import { artAssets, assetImage } from './art.ts';
import stages from '../design/prequel-maps.json' with {type:'json'};
import stages4 from '../design/chapter04-maps.json' with {type:'json'};
import travel from '../design/travel-maps.json' with {type:'json'};
const stageData={...stages,...stages4,...travel} as Record<string,{name:string;props:(string|number)[][]}>;
/** Books 1–4 carry a hand-written stage sheet with a chosen name and clear prop list.
 *  Books 5–6 have no such sheet — their stages exist only in the TMJ — so the name comes
 *  from the map's own `title` and the thumbnail is whatever that map stands tallest on
 *  screen: the hall roof of 会芳园, the stone arch of 迷津, the thatched gate of 刘家庄.
 *  Falling back to `spirit-stone` for all of them would have given six identical cards. */
type StageLook={title?:string;art?:readonly {asset:string;height:number}[]};
export function JourneyMap({chapter,sceneId,maps,onVisit}:{chapter:number;sceneId:string;maps?:Record<string,StageLook>;onVisit:(node:string)=>void}){
 const scenes=[...new Set(story.filter(s=>s.source.chapter===chapter).map(s=>s.scene))];
 return <div className="journey-map"><div className="journey-intro"><span>{bookNames[chapter]} · 行迹</span><p>按出场次序排列。梦境与现实分列，跨城行程不按距离比例绘制。</p></div><div className="journey-sites">{scenes.map((id,i)=>{const first=story.find(s=>s.source.chapter===chapter&&s.scene===id)!;const stage=stageData[id];const look=maps?.[id];const staged=stage?.props.find(p=>String(p[0]).startsWith('estate-'))?.[0]??(id==='lin'?'river-boat':id==='dream'?'crimson-pearl':undefined);const tallest=[...(look?.art??[])].sort((a,b)=>b.height-a.height)[0]?.asset;const art=artAssets[String(staged??tallest??'spirit-stone')];return <button key={id} className={id===sceneId?'journey-site current':'journey-site'} onClick={()=>onVisit(first.id)}><span className="journey-number">{String(i+1).padStart(2,'0')}</span>{art&&<img src={assetImage(art)} alt=""/>}<strong>{stage?.name??look?.title??first.place}</strong><small>{first.title}</small><span className="journey-enter">从此处开始 →</span></button>;})}</div></div>;
}
