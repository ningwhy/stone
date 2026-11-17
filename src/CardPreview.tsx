import { useEffect, useRef } from 'react';
import { artImage } from './art.ts';
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

/** 卡面上的人物立绘：**整幅全身像，不裁切**。
 *
 *  立绘是窄长的一幅（多数 600 高、190~350 宽），横版卡面塞不下全身——
 *  早先按 faceBox 裁头肩，看得见脸却看不见人；现在卡面改成竖版，
 *  整幅图缩进卡面高度里，从头顶到脚底都在。
 *  图鉴里的 Portrait 只认 cast 角色，而账上有些人是账簿专属的
 *  （娇杏、袭人、鹦哥、英莲——他们在账上被转手，却不是这场戏里的角色），
 *  所以这里直接按资产名取，用同一套资产表。 */
function PortraitFull({assetKey,alt}:{assetKey:string;alt:string}) {
  return <div className="card-face-portrait">
    <img className="card-face-img" src={artImage(assetKey)} alt={alt}/>
  </div>;
}

/** 卡面：只有画。卡名与副题在卡框下缘那一段，不压在画上。 */
function CardFace({card}:{card:CardPreviewData}) {
  return <div className={`card-face preview-face cat-${card.category}`}>
    {card.art==='portrait'&&card.artKey
      ?<PortraitFull assetKey={card.artKey} alt={`${card.title}的立绘`}/>
      :card.art==='goods'&&card.artSrc
        ?<img className="card-face-img" src={card.artSrc} alt={`${card.title}的货品图`}/>
        :<span className="card-face-seal" aria-hidden="true"><span className="mono">{card.seal}</span></span>}
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
    {/* 卡牌摆在桌面上：左边是那张竖版卡，右边是这一张卡的账。
        两者都算内容，关闭按钮放在桌面右上角。 */}
    <div className="preview-inner">
      <button className="icon-button preview-close" aria-label="关闭卡片" onClick={onClose}><IconClose/></button>
      <div className="preview-stage">
        <div className={`preview-card cat-${card.category}`}>
          <div className="preview-card-top">
            <span className="preview-kind">{categoryNames[card.category]}</span>
            <span className="preview-cost">{card.got}/{card.total}</span>
          </div>
          <div className="preview-card-art">
            <CardFace card={card}/>
          </div>
          <div className="preview-card-foot">
            <strong>{card.title}</strong>
            <small>{card.subtitle}</small>
          </div>
        </div>
      </div>
      <div className="preview-panel">
        <header className="preview-header">
          <span className="preview-kicker">背包 · {categoryNames[card.category]}</span>
        </header>
        <div className="preview-body">
          <p className="preview-ledger">
            <b>{card.got}/{card.total}</b> 笔入账
            {books.length>0&&<span className="preview-books"> · 出场于 {books.join('、')}</span>}
          </p>
          <section className="preview-flows">
            <h3 className="card-book-title">流转时间线</h3>
            {card.flows.map(flow=><FlowLine key={flow.id} flow={flow}/>)}
          </section>
        </div>
      </div>
    </div>
  </dialog>;
}

/** 关闭图标（与顶栏 Icon 同形，但这个组件不依赖 App.tsx 的内部组件）。 */
function IconClose() {
  return <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m6 6 12 12M6 18 18 6"/></svg>;
}
