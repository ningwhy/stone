import { useEffect, useRef } from 'react';
import { artAssets, artImage } from './art.ts';
import { bookNames } from './story.ts';
import type { CardPreview as CardPreviewData, CardFlow } from './cardPreview.ts';
import { flowLine } from './cardPreview.ts';
import { modeNames, categoryNames } from './ledger.ts';

/** 背包里的一张卡：像卡牌游戏那样，先看画，再看名，最后才看账。
 *
 *  三层信息分层——
 *  上层是卡面（大图 + 类别徽章 + 卡名 + 副题），
 *  中层是这一张卡的本事（有几笔账、涉哪几回），
 *  下层是流转时间线（谁 → 谁、什么方式、多少钱、哪一回、原文怎么写的）。
 *  未入账的账只留「？」，不提前泄露原文与情形。
 *
 *  这层用**独立的原生 dialog**，不塞在册页那个 dialog 里：原生 dialog 走
 *  浏览器顶层（top layer），盖在册页之上不会被册页的滚动容器裁掉；
 *  而放在册页内的定位层会被 dialog 的 overflow 与层叠上下文吃掉。 */

/** 按 manifest 的 faceBox 裁出的头部近景。
 *  图鉴里的 Portrait 只认 cast 角色，而账上有些人是账簿专属的
 *  （娇杏、袭人、鹦哥、英莲——他们在账上被转手，却不是这场戏里的角色），
 *  所以这里直接按资产名裁，用同一套算法。 */
function PortraitCloseup({assetKey,alt}:{assetKey:string;alt:string}) {
  const asset=artAssets[assetKey];
  const box=asset?.identity?.faceBox;
  if(!asset||!box) return <img className="card-face-img" src={artImage(assetKey)} alt={alt}/>;
  const h=(box[3]-box[1])*2.25,top=Math.max(0,box[1]-(box[3]-box[1])*.48),cx=(box[0]+box[2])/2;
  const shift=-(cx/asset.width*100);
  return <div className="card-face-portrait">
    <img className="card-face-img" src={artImage(assetKey)} alt={alt}
      style={{height:`${asset.height/h*100}%`,width:'auto',maxWidth:'none',left:'50%',top:`${-top/h*100}%`,transform:`translateX(${shift}%)`}}/>
  </div>;
}

/** 卡面：画铺满，徽章与卡名压在下缘（沿用册页卡片的墨色渐变）。 */
function CardFace({card}:{card:CardPreviewData}) {
  return <div className={`card-face preview-face cat-${card.category}`}>
    {card.art==='portrait'&&card.artKey
      ?<PortraitCloseup assetKey={card.artKey} alt={`${card.title}的立绘`}/>
      :card.art==='goods'&&card.artSrc
        ?<img className="card-face-img" src={card.artSrc} alt={`${card.title}的货品图`}/>
        :<span className="card-face-seal" aria-hidden="true"><span className="mono">{card.seal}</span></span>}
    <span className="preview-badge">{card.badge}</span>
    <div className="preview-title">
      <strong>{card.title}</strong>
      <small>{card.subtitle}</small>
    </div>
  </div>;
}

/** 流转时间线上的一笔。 */
function FlowLine({flow}:{flow:CardFlow}) {
  if(!flow.unlocked) return <article className="preview-flow locked">
    <span className="ledger-mode muted">？</span>
    <div className="preview-flow-main"><strong>？？？</strong><small>读到这一笔的剧情后入账</small></div>
  </article>;
  return <article className={`preview-flow mode-${flow.mode}`}>
    <span className={`ledger-mode ${flow.mode}`}>{modeNames[flow.mode]}</span>
    <div className="preview-flow-main">
      <strong>{flow.what}</strong>
      <small>{flowLine(flow)}</small>
      <p className="preview-flow-circ">{flow.circumstance}</p>
      {flow.source&&<blockquote className="preview-flow-source">{flow.source}</blockquote>}
    </div>
    <span className="card-seal">{bookNames[flow.book]??`第${flow.book}回`}</span>
  </article>;
}

export function CardPreview({card,onClose}:{card:CardPreviewData;onClose:()=>void}) {
  const ref=useRef<HTMLDialogElement>(null);
  // 用原生 dialog 的顶层：showModal 让它盖在册页之上，且 Esc 由 onCancel 接管。
  useEffect(()=>{
    const node=ref.current;
    if(!node) return;
    if(!node.open) node.showModal();
    return ()=>{ if(node.open) node.close(); };
  },[]);
  const books=card.books.map(b=>bookNames[b]??`第${b}回`);
  return <dialog ref={ref} className="preview-dialog" aria-label={`${card.title}的卡片`}
    onCancel={event=>{event.preventDefault();onClose();}}
    onClick={event=>{if(event.target===event.currentTarget)onClose();}}>
    <div className="preview-inner">
      <header className="preview-header">
        <span className="preview-kicker">背包 · {categoryNames[card.category]}</span>
        <button className="icon-button" aria-label="关闭卡片" onClick={onClose}><IconClose/></button>
      </header>
      <CardFace card={card}/>
      <div className="preview-body">
        <p className="preview-ledger">
          {card.got}/{card.total} 笔入账
          {books.length>0&&<span className="preview-books"> · 出场于 {books.join('、')}</span>}
        </p>
        <section className="preview-flows">
          <h3 className="card-book-title">流转时间线</h3>
          {card.flows.map(flow=><FlowLine key={flow.id} flow={flow}/>)}
        </section>
      </div>
    </div>
  </dialog>;
}

/** 关闭图标（与顶栏 Icon 同形，但这个组件不依赖 App.tsx 的内部组件）。 */
function IconClose() {
  return <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m6 6 12 12M6 18 18 6"/></svg>;
}
