import { cast } from './story.ts';
import type { ActorId, Move } from './story.ts';
import type { MapData } from './model.ts';
import type { StoryEngine } from './engine.ts';

/** Anchor ids are engineering names; the readable names live in map labels (specific) and
 * plan zones (coarse). Resolve once per map: nearest label wins, zone name as fallback. */
const nameCache=new Map<string,Record<string,string>>();
function anchorNames(map:MapData) {
  const cached=nameCache.get(map.id);
  if(cached)return cached;
  const names:Record<string,string>={};
  for(const [id,p] of Object.entries(map.anchors)) {
    let best:{text:string;dist:number}|null=null;
    for(const label of map.labels) {
      const dist=Math.hypot(label.point.col-p.col,label.point.row-p.row);
      if(dist<=2.5&&(!best||dist<best.dist))best={text:label.text,dist};
    }
    if(!best) {
      const zone=map.zones.find(z=>z.name&&p.col>=z.col&&p.col<z.col+z.width&&p.row>=z.row&&p.row<z.row+z.height);
      if(zone)best={text:zone.name,dist:0};
    }
    names[id]=best?.text??'';
  }
  nameCache.set(map.id,names);
  return names;
}

const EFFECT_TEXT={jade:'怒掷通灵玉',greet:'上前见礼',rest:'稍事歇息'} as const;

/** "大荒山 · 青埂峰（神话）" reads like a map title; stage talk wants "青埂峰". */
function shortPlace(name:string) {
  const part=name.includes('·')?name.split('·').at(-1)!:name;
  return part.replace(/（[^）]*）/g,'').trim();
}

/** One sentence of stage business for the action panel, derived from the live moves:
 * who walks, through which named places, towards which destination. People sharing one
 * route are merged into a single clause instead of a repetitive list. */
export function actionNarration(engine:StoryEngine) {
  const state=engine.getSnapshot();
  if(state.paused)return '演出暂停中，人物停在原地';
  if(state.effect)return `${cast[state.effect.actor].name}${EFFECT_TEXT[state.effect.kind]}`;
  const map=engine.map,names=anchorNames(map);
  const moves:Move[]=[];
  for(const action of engine.step.actions) {
    if(action.type==='move')moves.push(action);
    else if(action.type==='parallel')moves.push(...action.moves);
  }
  const moving=(Object.keys(state.actors) as ActorId[]).filter(id=>state.actors[id].visible&&state.actors[id].moving);
  const clauses:{who:string[];via:string[];dest?:string}[]=[];
  for(const id of moving) {
    const move=moves.find(m=>m.actor===id);
    if(!move)continue;
    const stops=move.via.map(a=>names[a]).filter(Boolean).map(shortPlace);
    const dest=stops.at(-1);
    const via=[...new Set(stops.slice(0,-1))].filter(name=>name&&name!==dest);
    const last=clauses.at(-1);
    if(last&&last.dest===dest&&last.via.join('|')===via.join('|'))last.who.push(cast[id].name);
    else clauses.push({who:[cast[id].name],via,dest});
  }
  if(!clauses.length)return '请看地图，好戏正在上演';
  return clauses.map(({who,via,dest}) => {
    const walkers=who.length>1?`${who.slice(0,-1).join('、')}与${who.at(-1)}`:who[0];
    const route=via.length?`经${via.join('、')}，`:'';
    return dest?`${walkers}${route}前往${dest}`:`${walkers}正沿路而行`;
  }).join('；');
}
