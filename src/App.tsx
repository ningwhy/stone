import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from 'react';
import Phaser from 'phaser';
import { MapScene } from './MapScene.ts';
import { SAVE_KEY, StoryEngine } from './engine.ts';
import { cast, story, chapters, bookNames } from './story.ts';
import type { ActorId } from './story.ts';
import { JourneyMap } from './JourneyMap.tsx';
import { Portrait } from './Portrait.tsx';
import { LoadingScreen, RotateHint, SceneLoadingCard } from './LoadingScreen.tsx';
import { prefetchCast, prefetchUpcoming } from './prefetch.ts';
import { WorldMap, worldLocations, travelRoute, worldLocationFor } from './WorldMap.tsx';
import type { Travel } from './WorldMap.tsx';

type Modal = 'history'|'settings'|'source'|'atlas'|'cast'|ActorId|null;
function Icon({name}: {name:string}) {
  const shapes:Record<string,string>={
    map:'M3 5 9 3l6 2 6-2v16l-6 2-6-2-6 2V5Zm6-2v16m6-14v16',
    book:'M4 4h6c2 0 2 1 2 2v15c0-2-1-3-3-3H4V4Zm16 0h-6c-2 0-2 1-2 2v15c0-2 1-3 3-3h5V4Z',
    compass:'m16 8-3 5-5 3 3-5 5-3Zm5 4a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z',
    arrow:'M5 12h14m-5-5 5 5-5 5',
    save:'M5 3h12l4 4v14H3V3h2Zm2 0v6h10V3M7 21v-8h10v8',
    reset:'M4 10a8 8 0 1 1 1 8M4 4v6h6',
    pause:'M8 5v14m8-14v14',
    play:'m8 4 12 8-12 8V4Z',
    settings:'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Zm0-6v3m0 14v3M2 12h3m14 0h3M5 5l2 2m10 10 2 2M5 19l2-2M17 7l2-2',
    close:'m6 6 12 12M6 18 18 6',
    chevron:'m9 5 7 7-7 7',
  };
  return <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={shapes[name]??shapes.compass}/></svg>;
}

function GameMap({engine,onScene,onActor,onProgress,onSnapshot,sceneId}: {sceneId:string;engine:StoryEngine;onScene:(scene:MapScene|null)=>void;onActor:(id:ActorId)=>void;onProgress:(value:number)=>void;onSnapshot:(dataUrl:string)=>void}) {
  const host=useRef<HTMLDivElement>(null);
  const snapshotRef=useRef(onSnapshot);snapshotRef.current=onSnapshot;
  useEffect(()=>{
    if(!host.current)return;
    const scene=new MapScene(engine,onActor);
    scene.onReady=ready=>{if(host.current)host.current.dataset.sceneReady=sceneId;onScene(ready);};
    scene.onProgress=onProgress;
    const game=new Phaser.Game({type:Phaser.CANVAS,parent:host.current,width:host.current.clientWidth,height:host.current.clientHeight,
      backgroundColor:'#eee8d7',antialias:true,scene:[scene],audio:{noAudio:true},
      scale:{mode:Phaser.Scale.RESIZE},render:{roundPixels:false}});
    const observer=new ResizeObserver(()=>{if(host.current)game.scale.resize(host.current.clientWidth,host.current.clientHeight);});
    observer.observe(host.current);
    // Keep the outgoing frame on screen while the next scene loads; a blank stage reads as a crash.
    return ()=>{
      const canvas=host.current?.querySelector('canvas') as HTMLCanvasElement|undefined;
      if(canvas?.width&&canvas.height){
        try{
          const scale=Math.min(1,560/canvas.width);
          const small=document.createElement('canvas');
          small.width=Math.max(1,Math.round(canvas.width*scale));
          small.height=Math.max(1,Math.round(canvas.height*scale));
          const context=small.getContext('2d');
          if(context){context.drawImage(canvas,0,0,small.width,small.height);snapshotRef.current(small.toDataURL('image/jpeg',.72));}
        }catch{/* canvas already recycled: fall back to the plain stage */ }
      }
      observer.disconnect();if(host.current)delete host.current.dataset.sceneReady;onScene(null);game.destroy(true);
    };
  },[engine,onActor,onScene,sceneId]);
  return <div className="game-map" ref={host} role="img" aria-label="40×40 格红楼梦等距场景，人物随剧情移动"/>;
}

export function App({engine,initialNotice=''}:{engine:StoryEngine;initialNotice?:string}) {
  const state=useSyncExternalStore(engine.subscribe,engine.getSnapshot);
  const step=engine.step;
  const [modal,setModal]=useState<Modal>(null),[automatic,setAutomatic]=useState(false),[showGuides,setShowGuides]=useState(false);
  const [notice,setNotice]=useState(initialNotice),[storageError,setStorageError]=useState('');
  const sceneRef=useRef<MapScene|null>(null),dialog=useRef<HTMLDialogElement>(null);
  const [savedLabel,setSavedLabel]=useState('');
  const [overview,setOverview]=useState(false),[travel,setTravel]=useState<Travel|null>(null);
  const [loadProgress,setLoadProgress]=useState(0),[loaded,setLoaded]=useState(false),[overlay,setOverlay]=useState(true);
  const [sceneProgress,setSceneProgress]=useState(0),[sceneReady,setSceneReady]=useState(false),[sceneSlow,setSceneSlow]=useState(false);
  const [snapshot,setSnapshot]=useState('');
  const readyRef=useRef(false);
  // Reset the per-scene stage whenever the story moves to another map. The card only shows if loading is slow,
  // so a cached scene never flashes one.
  useEffect(()=>{
    readyRef.current=false;setSceneProgress(0);setSceneReady(false);setSceneSlow(false);
    const timer=setTimeout(()=>{if(!readyRef.current)setSceneSlow(true);},260);
    return ()=>clearTimeout(timer);
  },[state.sceneId]);
  // Drop the outgoing frame once the new stage has painted.
  useEffect(()=>{if(!sceneReady||!snapshot)return;const timer=setTimeout(()=>setSnapshot(''),650);return ()=>clearTimeout(timer);},[sceneReady,snapshot]);
  // Warm what the next scenes will ask for while the reader is busy with this one.
  useEffect(()=>{
    if(!sceneReady)return;
    const timer=setTimeout(()=>{
      prefetchCast(engine,state.index);
      prefetchUpcoming(engine,state.index);
    },300);
    return ()=>clearTimeout(timer);
  },[sceneReady,state.index,state.sceneId,engine]);
  // A stuck Phaser boot must never trap the reader behind the first-paint stage.
  useEffect(()=>{if(loaded)return;const timer=setTimeout(()=>setLoaded(true),12000);return ()=>clearTimeout(timer);},[loaded]);
  useEffect(()=>{if(!loaded||!overlay)return;const timer=setTimeout(()=>setOverlay(false),600);return ()=>clearTimeout(timer);},[loaded,overlay]);
  const worldId=worldLocationFor(state.sceneId,state.focus);
  const previous=useRef({scene:worldId,index:state.index});
  useEffect(()=>{
    const prev=previous.current;previous.current={scene:worldId,index:state.index};
    if(prev.scene!==worldId && state.index===prev.index+1){const route=travelRoute(prev.scene,worldId);if(route)setTravel({...route,progress:0});}
    else if(prev.index!==state.index)setTravel(null);
  },[worldId,state.index]);
  useEffect(()=>{if(!travel||state.paused)return;const timer=setInterval(()=>setTravel(t=>t?(t.progress>=1?null:{...t,progress:Math.min(1,t.progress+.025*state.speed)}):null),50);return ()=>clearInterval(timer);},[!!travel,state.paused,state.speed]);
  const travelRef=useRef(false);travelRef.current=!!travel;
  const onScene=useCallback((scene:MapScene|null)=>{sceneRef.current=scene;if(scene){scene.presentationPaused=travelRef.current;scene.input.enabled=!document.querySelector('dialog[open]');setLoaded(true);readyRef.current=true;setSceneReady(true);}else{readyRef.current=false;}},[]);
  useEffect(()=>{if(sceneRef.current)sceneRef.current.presentationPaused=!!travel;},[travel,state.sceneId]);
  const onActor=useCallback((id:ActorId)=>setModal(id),[]);
  // The first-paint stage and the per-scene card share one loader signal.
  const onMapProgress=useCallback((value:number)=>{setLoadProgress(value);setSceneProgress(value);},[]);
  const save=useCallback(()=>{
    try {const data=engine.serialize();localStorage.setItem(SAVE_KEY,JSON.stringify(data));setSavedLabel(`已保存 · ${engine.step.title}`);setStorageError('');}
    catch(e){setStorageError(e instanceof Error?e.message:'无法保存进度');}
  },[engine]);
  useEffect(()=>{if(state.status==='reading'||state.status==='ended')save();},[state.index,state.status,save]);
  useEffect(()=>{
    engine.overlay(modal!==null);
    if(sceneRef.current)sceneRef.current.input.enabled=modal===null;
    if(modal && dialog.current && !dialog.current.open)dialog.current.showModal();
    if(!modal && dialog.current?.open)dialog.current.close();
  },[modal,engine]);
  useEffect(()=>{
    if(!automatic||travel||state.paused||state.status!=='reading')return;
    const timer=setTimeout(()=>engine.advance(),Math.max(3800,step.text.length*130));
    return ()=>clearTimeout(timer);
  },[automatic,state.paused,state.status,state.index,step.text,engine,travel]);
  useEffect(()=>{
    const handler=(event:KeyboardEvent)=>{
      if(event.code!=='Space'||event.repeat||modal||travel||['BUTTON','INPUT','SELECT','TEXTAREA'].includes((event.target as HTMLElement)?.tagName))return;
      event.preventDefault();engine.advance();
    };
    window.addEventListener('keydown',handler);return ()=>window.removeEventListener('keydown',handler);
  },[engine,modal,travel]);
  useEffect(()=>{if(!notice)return;const t=setTimeout(()=>setNotice(''),4500);return ()=>clearTimeout(t);},[notice]);
  const load=()=>{
    try {const value=localStorage.getItem(SAVE_KEY);if(!value)throw new Error('还没有保存的进度');engine.restore(JSON.parse(value));setAutomatic(false);setNotice('已恢复地图与对白进度');}
    catch(e){setNotice(e instanceof Error?e.message:'读取失败');}
  };
  const restart=()=>{setAutomatic(false);engine.restart();sceneRef.current?.recenter();setNotice('已回到第一回开篇');};
  const portrait:ActorId=step.speaker==='narrator'?(state.actors.daiyu.visible?'daiyu':(Object.keys(cast) as ActorId[]).find(id=>state.actors[id].visible&&id!=='sedan')??'daiyu'):step.speaker;
  const progress=Math.round(state.index/(story.length-1)*100);
  const inMotion=state.status==='moving'||!!travel,ended=state.status==='ended';
  useEffect(()=>{if(inMotion)sceneRef.current?.recenter();},[inMotion,state.index]);
  const present=(Object.keys(state.actors) as ActorId[]).filter(id=>state.actors[id].visible && id!=='sedan');
  const listeners=present.filter(id=>id!==portrait);
  const [listenerOffset,setListenerOffset]=useState(0);
  const listener=listeners[listenerOffset%Math.max(listeners.length,1)];
  const character=modal && modal in cast ? cast[modal as ActorId] : null;

  return <main className="app-shell">
    {overlay&&<LoadingScreen progress={loadProgress} done={loaded}/>}
    <RotateHint/>
    <header className="app-header">
      <a className="brand" href="./" aria-label="红楼一隅首页"><span className="brand-seal">红</span><span>红楼一隅</span></a>
      <select className="chapter-select" aria-label="选择剧情段落" value={step.chapter} onChange={e=>{const chapter=chapters.find(c=>c.id===e.target.value)!;setAutomatic(false);setTravel(null);engine.seek(chapter.start);}}>{[1,2,3].map(book=><optgroup label={bookNames[book]} key={book}>{chapters.filter(c=>c.book===book).map(c=><option value={c.id} key={c.id}>{bookNames[book]} · {c.title}</option>)}</optgroup>)}</select>
      <span className="reading-progress" title={`${state.index+1} / ${story.length}`}>{progress}%<progress max="100" value={progress} aria-label="前三回剧情进度"/></span>
      <nav className="playback-controls" aria-label="演出控制">
        <button className={automatic?'text-button selected':'text-button'} aria-pressed={automatic} onClick={()=>setAutomatic(!automatic)}><Icon name="play"/>自动</button>
        <button className="text-button" onClick={()=>setModal('history')}><Icon name="book"/>回看</button>
        <button className="text-button" onClick={()=>engine.pause(!state.paused)} disabled={state.status==='error'}><Icon name={state.paused?'play':'pause'}/>{state.paused?'继续演出':'暂停'}</button>
        {ended?<button className="next-button" onClick={restart}>再走一回 <Icon name="reset"/></button>:inMotion?<button className="next-button secondary" disabled={state.paused} onClick={()=>{if(travel)setTravel(null);else engine.skip();}}>跳过移动 <Icon name="chevron"/></button>:<button className="next-button" disabled={state.paused||state.status==='error'} onClick={()=>engine.advance()}>继续剧情 <Icon name="arrow"/></button>}
        <button className="icon-button" aria-label="设置" onClick={()=>setModal('settings')}><Icon name="settings"/></button>
      </nav>
    </header>
    <div className="story-stage">
        <section className={`map-panel ${inMotion?'map-action':''}`} aria-label="地图演出" data-paused={state.paused}>
          <div className={overview||travel?'local-map concealed':'local-map'}>
            {snapshot&&<img className="map-snapshot" src={snapshot} alt="" aria-hidden="true" data-fade={sceneReady}/>}
            <GameMap sceneId={state.sceneId} engine={engine} onScene={onScene} onActor={onActor} onProgress={onMapProgress} onSnapshot={setSnapshot}/>
            {!sceneReady&&sceneSlow&&<SceneLoadingCard title={engine.maps[state.sceneId]?.title??step.place} progress={sceneProgress}/>}
          </div>
          {overview&&step.source.chapter<3?<JourneyMap chapter={step.source.chapter} sceneId={state.sceneId} onVisit={node=>{setOverview(false);setAutomatic(false);engine.seek(node);}}/>:(overview||travel)&&<WorldMap sceneId={worldId} travel={travel} onVisit={id=>{const place=worldLocations.find(l=>l.id===id);const target=place?.start?story.find(s=>s.id===place.start):story.find(s=>s.source.chapter===3&&s.scene===(place?.scene??id));if(target){setTravel(null);setOverview(false);setAutomatic(false);engine.seek(target.id);}}}/>}
          <div className="map-navigation">
            <div className="view-switch" aria-label="地图视图"><button aria-pressed={!overview&&!travel} onClick={()=>{setTravel(null);setOverview(false);}}>当前场景</button><button aria-pressed={overview||!!travel} onClick={()=>setOverview(true)}>{step.source.chapter<3?'本回行迹':'荣国府总览'}</button></div>
            <span className="current-place">{travel?`${worldLocations.find(l=>l.id===travel.from)?.name} → ${worldLocations.find(l=>l.id===travel.to)?.name}`:step.place}</span>
          </div>
          {!overview&&!travel&&<div className="map-tools" onPointerDown={e=>e.stopPropagation()}><button title="缩小" aria-label="缩小地图" onClick={()=>sceneRef.current?.zoom(-.15)}>−</button><button title="回到剧情" aria-label="回到剧情镜头" onClick={()=>sceneRef.current?.recenter()}><Icon name="compass"/></button><button title="放大" aria-label="放大地图" onClick={()=>sceneRef.current?.zoom(.15)}>＋</button></div>}
          {!overview&&!travel&&<span className="local-compass" aria-label="地图方位：北向右上，东向右下">北 ↗<br/>东 ↘</span>}
          {inMotion&&<div className="map-action-cue" role="status"><span className="action-orbit"/><span>{state.paused?'行动已暂停':travel?'黛玉正在地点之间移动':'跟随人物 · '+step.title}</span></div>}
          {state.paused&&<div className="paused-label"><Icon name="pause"/>演出已暂停</div>}
        </section>
        <section className={`dialogue-panel ${inMotion?'action-mode':'conversation-mode'} ${overview||travel?'stage-overview':''}`} aria-label="剧情对话" data-mode={inMotion?'action':'dialogue'} data-paused={state.paused}>
          {!inMotion&&<>
            <div className="speaker-portrait" key={portrait}><Portrait actor={portrait} sad={step.mood==='sad'}/><span className="portrait-role">{step.speaker==='narrator'?'故事视角':'讲话人'}</span></div>
            {listener&&<div className="listener-portraits" aria-label="在场人物立绘">
              <div className="listener-stack" aria-hidden="true">{listeners.filter(id=>id!==listener).slice(0,2).map(id=><div key={id}><Portrait actor={id} closeup/></div>)}</div>
              <button className="listener-feature" onClick={()=>setModal(listener)} aria-label={`查看${cast[listener].fullName}资料`}><Portrait actor={listener}/><span>{cast[listener].name}</span></button>
              <div className="listener-picker" aria-label="切换在场立绘">{listeners.map((id,i)=><button key={id} className={listener===id?'active':''} onClick={()=>setListenerOffset(i)} aria-label={`显示${cast[id].fullName}立绘`} aria-pressed={listener===id}>{cast[id].name}</button>)}</div>
            </div>}
          </>}
          <div className="dialogue-body">
            <div className="speaker-line"><span className="speaker-rule"/><h2>{inMotion?'行 动':step.speaker==='narrator'?'旁白':cast[step.speaker].fullName}</h2><span className="dialogue-type">{inMotion?'地图演出':step.offscreen?'画外':step.speaker==='narrator'?'叙事':'对白'}</span>{step.source.layer&&step.source.layer!=='present'&&<span className="narrative-layer">{({dream:'梦境',recollection:'回忆',reported:'转述'} as Record<string,string>)[step.source.layer]}</span>}<span className="node-label">{step.id==='END'?'终幕':step.id}</span></div>
            {inMotion?<div className="action-presentation" aria-live="polite"><div className="action-path-motif"><i/><i/><i/><Icon name="compass"/></div><div><strong>{travel?'穿院而行':step.title}</strong><p>{travel?'沿府内道路前往下一处':state.paused?'演出暂停中':'请看地图，'+(state.effect?cast[state.effect.actor].name:present.filter(id=>state.actors[id].moving).map(id=>cast[id].name).join('、'))+'正在行动'}</p></div><span className="action-direction">视线回到地图 ↑</span></div>:<p className="dialogue-text" aria-live="polite">{step.text}</p>}
            {state.status==='error'&&<p className="error-message" role="alert">{state.error}</p>}
          </div>
        </section>
    </div>
    {notice&&<div className="toast" role="status">{notice}</div>}
    <dialog ref={dialog} onCancel={event=>{event.preventDefault();setModal(null);}} onClick={event=>{if(event.target===dialog.current)setModal(null);}}>
      <div className="modal-header"><h2>{modal==='history'?'对白回看':modal==='settings'?'阅读设置':modal==='source'?'原文与改编':modal==='atlas'?'前三回 · 地图地点':modal==='cast'?'前三回 · 人物图鉴':character?.fullName}</h2><button className="icon-button" aria-label="关闭弹窗" onClick={()=>setModal(null)}><Icon name="close"/></button></div>
      {modal==='history'&&<div className="history-list">{state.history.map(entry=><article key={entry.id}><span>{entry.speaker}<small>{entry.id}</small></span><p>{entry.text}</p></article>)}</div>}
      {modal==='settings'&&<div className="settings-body"><p>{storageError||savedLabel}</p><div className="save-actions"><button className="text-button" onClick={save} disabled={inMotion}>保存</button><button className="text-button" onClick={()=>{setModal(null);load();}}>读取</button><button className="text-button" onClick={()=>{setModal(null);restart();}}>重玩</button><button className="text-button" onClick={()=>setModal('source')}>原文与改编</button><button className="text-button" onClick={()=>setModal('atlas')}>地图地点</button><button className="text-button" onClick={()=>setModal('cast')}>人物图鉴</button></div><label>人物行走速度<select value={state.speed} onChange={e=>engine.setSpeed(Number(e.target.value))}><option value="0.5">慢行 · 0.5 倍</option><option value="1">常速 · 1 倍</option><option value="2">快行 · 2 倍</option></select></label><label className="check-label"><input type="checkbox" checked={showGuides} onChange={e=>{setShowGuides(e.target.checked);sceneRef.current?.guides(e.target.checked);}}/>显示地图上的引导路线</label><p>打开设置、人物信息或对白记录时，演出会暂停。关闭后保留之前的暂停状态。</p><p>进度在每条对白到达后自动保存，刷新页面会恢复。隐私浏览或存储限制可能使保存失败。</p></div>}
      {modal==='source'&&<div className="source-body"><span className="source-badge">{bookNames[step.source.chapter]} · 完整剧情改编</span><p>前三回覆盖石头来历、绛珠还泪、甄家兴衰、雨村仕途、冷子兴演说，以及黛玉入府全程。第一、二回的梦境、回忆和转述均另作标识，人物不会因此出现在当下场景。</p><p>底本参考维基文库《红楼梦》第一至三回，正文已存入项目资料。除诗词和少量短句，页面文字为便于交互阅读的改写；空间布局、尺度与演出为设计补充。</p><p>当前节点：{step.id}；对应原文段落起句：“{step.source.paragraphLead}”。</p><p>地图均为 40×40 等距舞台。总览以列增为东、行增为南；西角门按西墙方案布置，黑油大门开在南墙偏东。西角门具体墙面是设计选择，原文明确的是去程出西角门、往东过正门、入黑油大门的顺序；回程门名未明示，本版选择由正门进入。原文中仅被提及、没有实际到访的地点不安排人物进入；第三回宝玉庙里还愿与贾政斋戒只作叙述。</p><p>美术由本地 ComfyUI 生成，经抠图与定位校准接入。服饰与建筑为原创视觉演绎，有形出场的人物均配有立绘与 Q 版图像；只在谈话中提及的家族成员保留为转述。</p></div>}
      {modal==='atlas'&&<div className="atlas-body">{Object.values(engine.maps).map(map=><article key={map.id}><h3>{map.title}</h3><p>{map.labels.length?map.labels.map(l=>l.text).join(' · '):'西角门 · 换轿处 · 垂花门 · 穿堂插屏 · 贾母正房 · 后房门'}</p><small>40×40 格 · {Object.keys(map.anchors).length} 个剧情地点</small></article>)}<p className="atlas-note">金陵应天府、还愿庙宇、斋戒处为叙述提及，不是本回黛玉实际到访的场景。</p></div>}

      {modal==='cast'&&<div className="cast-gallery">{(Object.keys(cast) as ActorId[]).filter(id=>id!=='sedan').map(id=><article key={id}>
        <button className="gallery-portrait" aria-label={`查看${cast[id].fullName}资料`} onClick={()=>setModal(id)}><Portrait actor={id} closeup/></button>
        <strong>{cast[id].fullName}</strong><small>{cast[id].relation}</small>
        <button className="text-button" onClick={()=>{const first=story.find(s=>s.actions.some(a=>a.type==='show'&&a.actor===id));if(first){setModal(null);setAutomatic(false);setOverview(false);setTravel(null);engine.seek(first.id);}}}>定位出场 →</button>
      </article>)}</div>}
      {character&&<div className="character-detail"><div className="mini-portrait"><Portrait actor={modal as ActorId} closeup/></div><div><span className="source-badge">{character.relation}</span><p>{character.description}</p><small>人物资料与原文文本仍待底本校订。</small></div></div>}
      <div className="modal-footer"><span>阅读时，地图演出已暂停</span><button className="next-button" onClick={()=>setModal(null)}>返回故事 <Icon name="arrow"/></button></div>
    </dialog>
  </main>;
}
