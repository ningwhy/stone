import { artAssets, artImage } from './art.ts';
import { cast, paintedFacingOf } from './story.ts';
import type { ActorId } from './story.ts';
import type { Emotion } from './emotion.ts';

/** Painted faces arrive over the network; mark them so CSS can fade in instead of flashing an empty box. */
function painted(key: string, actor: ActorId, style?: React.CSSProperties) {
  const done = (element: HTMLImageElement | null) => { if (element && element.complete) element.dataset.loaded = 'true'; };
  return <img
    ref={done}
    src={artImage(key)}
    className="portrait-svg portrait-painted"
    alt={`${cast[actor].fullName}手绘立绘`}
    style={style}
    onLoad={event => { event.currentTarget.dataset.loaded = 'true'; }}
    onError={event => { event.currentTarget.dataset.loaded = 'true'; }}
  />;
}

/** Shared painted identity, with a close-up frame for the cast directory. Emotion variants
 * fall back to the neutral portrait whenever the pair has not been generated yet. */
export function Portrait({actor, sad=false, closeup=false, face, emotion}: {actor:ActorId; sad?:boolean; closeup?:boolean; face?:'left'|'right'; emotion?:Emotion}) {
  const key=emotion&&emotion!=='neutral'&&artAssets[`${actor}-portrait-${emotion}`]?`${actor}-portrait-${emotion}`:`${actor}-portrait`,asset=artAssets[key];
  if(asset){
    const box=asset.identity?.faceBox;
    // The portrait is painted facing one side; showing it on the other side of
    // the panel needs a mirror so it looks towards the speaker or the text.
    // An emotion variant is a separately painted bitmap, so it is looked up by
    // its own key — the variants do not all face the same way.
    const base=paintedFacingOf(key,actor,'portrait');
    const mirrored=face!==undefined&&face!==base;
    if(closeup&&box){
      const h=(box[3]-box[1])*2.25,top=Math.max(0,box[1]-(box[3]-box[1])*.48),cx=(box[0]+box[2])/2;
      const shift=mirrored?-(asset.width-cx)/asset.width*100:-cx/asset.width*100;
      return <div className="portrait-closeup">{painted(key,actor,{height:`${asset.height/h*100}%`,width:'auto',maxWidth:'none',left:'50%',top:`${-top/h*100}%`,transform:`translateX(${shift}%)${mirrored?' scaleX(-1)':''}`})}</div>;
    }
    return painted(key,actor,mirrored?{transform:'scaleX(-1)'}:undefined);
  }
  const color=cast[actor].css, elder=actor==='grandmother', hair=elder?'#8b8980':'#3d4842';
  return <svg viewBox="0 50 220 250" role="img" aria-label={`${cast[actor].name}立绘占位`} className="portrait-svg">
    <ellipse cx="111" cy="164" rx="85" ry="112" fill={color} opacity=".09"/>
    <path d="M54 300 62 226Q68 207 93 202L127 202Q156 205 163 226L178 300" fill={color}/>
    <path d="M93 182 92 209 111 231 131 208 127 181" fill="#ead6bb"/>
    <path d="M91 205 111 232 97 258 73 215M130 205 110 233 127 265 150 216" fill="#e8e2ce"/>
    <path d="M109 236 127 265 114 300H91" fill={color} opacity=".8"/>
    <path d="M81 223 68 300M145 223 162 300" fill="none" stroke="#f2e7ce" strokeWidth="2" opacity=".6"/>
    <path d="M65 135Q48 88 75 66Q107 43 140 65Q174 88 155 144L148 192 76 194" fill={hair}/>
    <ellipse cx="110" cy="137" rx="42" ry="55" fill="#f0dfc6"/>
    <ellipse cx="70" cy="143" rx="7" ry="12" fill="#ecd6ba"/><ellipse cx="151" cy="143" rx="7" ry="12" fill="#ecd6ba"/>
    <path d="M68 123Q67 79 102 79Q144 69 153 123Q129 111 121 88Q99 114 68 123" fill={hair}/>
    <ellipse cx="72" cy="93" rx="18" ry="22" fill={hair}/><ellipse cx="148" cy="92" rx="19" ry="23" fill={hair}/>
    <path d={sad?'M84 133Q92 128 99 133M120 133Q128 128 135 133':'M84 131Q92 127 99 131M120 131Q128 127 135 131'} stroke="#6d695c" strokeWidth="2" fill="none"/>
    <path d="M85 141Q92 138 99 141M121 141Q128 138 135 141" fill="none" stroke="#4e5147" strokeWidth="2"/>
    <ellipse cx="93" cy="142" rx="2.2" ry="3" fill="#4b5046"/><ellipse cx="128" cy="142" rx="2.2" ry="3" fill="#4b5046"/>
    <path d="M109 146 106 157 112 158" fill="none" stroke="#cbb092" strokeWidth="1.4"/>
    <path d={sad?'M103 171Q110 167 118 171':'M103 168Q111 173 118 168'} fill="none" stroke="#b78777" strokeWidth="2"/>
    <ellipse cx="86" cy="156" rx="9" ry="5" fill="#d5a38f" opacity=".2"/><ellipse cx="134" cy="156" rx="9" ry="5" fill="#d5a38f" opacity=".2"/>
    <path d="M69 92 47 86M144 84 169 78" stroke="#c3ab70" strokeWidth="3"/>
    <circle cx="165" cy="79" r="5" fill="#d0b77f"/><circle cx="67" cy="154" r="3" fill="#c3ab70"/><circle cx="154" cy="154" r="3" fill="#c3ab70"/>
    {elder && <><path d="M80 152 94 153M127 153 140 152" stroke="#c4ae96" fill="none"/><path d="M98 165 96 173M124 165 127 173" stroke="#c4ae96"/></>}
    <path d="M76 273 145 273" stroke="#d4c29c" strokeWidth="6"/><path d="M113 275V298" stroke="#d4c29c" strokeWidth="3"/>
  </svg>;
}
