import { useCallback, useEffect, useMemo, useRef, useState, useSyncExternalStore } from 'react';
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
import { actionNarration } from './narration.ts';
import { emotionOf } from './emotion.ts';
import { audio } from './audio.ts';
import { cards, cardsByBook, loadStored, saveStored, sceneIndex, bondCards, tokenCards, unlockedCards } from './collection.ts';
import { ledgerEntries, loadStoredLedger, saveStoredLedger, unlockedLedger, ledgerActors, ledgerFor, ledgerItemTraces, modeNames, categoryNames } from './ledger.ts';
import type { LedgerEntry } from './ledger.ts';

type Modal = 'history'|'settings'|'source'|'atlas'|'cast'|ActorId|null;
function LedgerRow({entry,got,label}:{entry:LedgerEntry;got:boolean;label:string}) {
  const seal=bookNames[entry.book]??`第${entry.book}回`;
  return <article className={`ledger-row mode-${entry.mode} ${got?'unlocked':'locked'}`} aria-label={got?label:'未入账的一笔'}>
    {got?<>
      <span className={`ledger-mode ${entry.mode}`}>{modeNames[entry.mode]}</span>
      <div className="ledger-main">
        <strong>{entry.what}</strong>
        <small className="ledger-flow">{label}{entry.amount!=null?` · ${entry.amount} 两`:''}</small>
        <p className="ledger-circ">{entry.circumstance}</p>
      </div>
      <span className="card-seal">{seal}</span>
    </>:<><span className="ledger-mode muted">？</span><div className="ledger-main"><strong>？？？</strong><small>读到这一笔的剧情后入账</small></div></>}
  </article>;
}
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
    sound:'M4 9v6h4l5 4V5L8 9H4Zm12.5 3a4.5 4.5 0 0 0-2.5-4v8a4.5 4.5 0 0 0 2.5-4Zm-2.5-7.7v2.1a7 7 0 0 1 0 13.2v2.1a9 9 0 0 0 0-17.4Z',
    bag:'M6 8V6a6 6 0 0 1 12 0v2m-15 0h18l-1.2 11.1a2 2 0 0 1-2 1.9H6.2a2 2 0 0 1-2-1.9L3 8Zm6 4a3 3 0 0 0 6 0',
    mute:'M4 9v6h4l5 4V5L8 9H4Zm15.5 0L17 11.5 15.5 13l1.5 1.5L18.5 13 20 14.5 21.5 13 19.5 11.5 21 10 19.5 8.5 18.5 10 17 8.5Z',
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
  // The master sound switch and the auto-play toggle are one idea each: a single switch
  // that reads as what it currently does. `automatic` means the story advances itself, so
  // the same button reads 暂停 while it is on -- and pressing it then stops the story
  // rather than leaving the reader stuck behind a button that looks live but does nothing.
  const [muted,setMuted]=useState(()=>audio.muted);
  const [notice,setNotice]=useState(initialNotice),[storageError,setStorageError]=useState('');
  const sceneRef=useRef<MapScene|null>(null),dialog=useRef<HTMLDialogElement>(null);
  const [savedLabel,setSavedLabel]=useState('');
  // 册页（收集）是引擎的旁挂：解锁只从 readLog 推导，另外单独存一份
  // 「我在这部书里见过什么」——换存档重读时收集记录仍在。
  const [atlasTab,setAtlasTab]=useState<'maps'|'cards'|'ledger'>('maps');
  const sceneIdx=useMemo(()=>sceneIndex(engine.steps),[engine]);
  const storedCards=useMemo(()=>loadStored(),[]);
  const unlocked=useMemo(()=>unlockedCards(state.readLog??[],sceneIdx,storedCards),[state.readLog,sceneIdx,storedCards]);
  const tokens=useMemo(()=>tokenCards(),[]);
  const bonds=useMemo(()=>bondCards(),[]);
  useEffect(()=>{saveStored(unlocked);},[unlocked.size]); // 只在收集增长时写盘
  // 账簿与卡片同源：读到节点即入账，另有自己的「见过的账」存档。
  const [ledgerPerson,setLedgerPerson]=useState<string|null>(null);
  const [ledgerView,setLedgerView]=useState<'people'|'items'>('people');
  const [ledgerItem,setLedgerItem]=useState<string|null>(null);
  const [storedLedger,setStoredLedger]=useState<string[]>(()=>loadStoredLedger());
  const ledgerUnlocked=useMemo(()=>unlockedLedger(state.readLog??[],storedLedger),[state.readLog,storedLedger]);
  const ledgerPeople=useMemo(()=>ledgerActors(),[]);
  const ledgerItems=useMemo(()=>ledgerItemTraces(),[]);
  const personBook=useMemo(()=>ledgerPerson?ledgerFor(ledgerPerson):null,[ledgerPerson]);
  const itemBook=useMemo(()=>ledgerItem?ledgerItems.find(t=>t.key===ledgerItem)??null:null,[ledgerItem,ledgerItems]);
  useEffect(()=>{saveStoredLedger(ledgerUnlocked);},[ledgerUnlocked.size]);
  // 获得弹窗：读到有「交到手上」的节点时，像游戏捡道具一样展示货品并请读者收下。
  // 只认存档里还没见过的账；确认后写入存档，重读、跳回、刷新都不会再弹。
  const [pickup,setPickup]=useState<LedgerEntry[]|null>(null);
  const storedLedgerRef=useRef(storedLedger);storedLedgerRef.current=storedLedger;
  useEffect(()=>{
    const fresh=ledgerEntries.filter(e=>e.node===step.id&&!storedLedgerRef.current.includes(e.id));
    if(fresh.length)setPickup(fresh);
  },[step.id]); // 故意只盯节点变化：存档在确认时才更新，避免二次触发
  const takePickup=()=>{
    if(pickup){
      const ids=pickup.map(e=>e.id);
      setStoredLedger(prev=>[...new Set([...prev,...ids])]);
      saveStoredLedger(new Set([...loadStoredLedger(),...ids]));
      audio.play('sfx-page',1);
    }
    setPickup(null);
  };
  const [overview,setOverview]=useState(false),[travel,setTravel]=useState<Travel|null>(null);
  const [loadProgress,setLoadProgress]=useState(0),[loaded,setLoaded]=useState(false),[overlay,setOverlay]=useState(true);
  const [sceneProgress,setSceneProgress]=useState(0),[sceneReady,setSceneReady]=useState(false),[sceneSlow,setSceneSlow]=useState(false);
  const [snapshot,setSnapshot]=useState('');
  const [audioPrefs,setAudioPrefs]=useState(()=>audio.getPrefs());
  const readyRef=useRef(false);
  // Browsers keep an AudioContext suspended until the reader touches something, so the
  // soundtrack starts on the first gesture rather than silently failing to start at all.
  useEffect(()=>{
    const start=()=>audio.unlock();
    window.addEventListener('pointerdown',start,{once:true});
    window.addEventListener('keydown',start,{once:true});
    return()=>{window.removeEventListener('pointerdown',start);window.removeEventListener('keydown',start);};
  },[]);
  // The piece follows the stage: garden by day, the market outside the wall, water on the
  // canal, quieter indoors, bowls for the mythic scenes. Same-theme moves are a no-op, so
  // walking between rooms does not restart it.
  useEffect(()=>{
    const theme=engine.maps[state.sceneId]?.theme??'garden';
    // The chapter decides the music: each of the four books has a piece of its own, and
    // the scene theme only takes over where a stage has music of its own.
    const book=chapters.find(c=>c.id===step.chapter)?.book;
    audio.setTheme(theme,state.sceneId,book);
    // Arriving under a roof is audible before it is visible: the door was the one effect
    // the renderer preloaded and nothing ever played.
    if(theme==='interior'||theme==='formal')audio.play('sfx-door',2);
  },[state.sceneId,engine,step.chapter]);
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
  const onScene=useCallback((scene:MapScene|null)=>{sceneRef.current=scene;if(scene){scene.presentationPaused=travelRef.current;scene.input.enabled=!document.querySelector('dialog[open]');setLoaded(true);readyRef.current=true;setSceneReady(true);
    // QA hook: the browser smoke tests read the live stage through this handle.
    (window as unknown as {__mapScene?:MapScene}).__mapScene=scene;
  }else{readyRef.current=false;delete (window as unknown as {__mapScene?:MapScene}).__mapScene;}},[]);
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
    engine.overlay(modal!==null||pickup!==null);
    if(sceneRef.current)sceneRef.current.input.enabled=modal===null&&pickup===null;
    if(modal && dialog.current && !dialog.current.open)dialog.current.showModal();
    if(!modal && dialog.current?.open)dialog.current.close();
  },[modal,pickup,engine]);
  useEffect(()=>{
    // Opening a panel pauses the performance through the engine's overlay flag, which
    // would otherwise switch the auto-play off as a side effect of looking at the
    // settings. The reader's own choice is kept: auto resumes when the panel closes.
    if(!automatic||travel||state.paused||state.status!=='reading'||pickup)return;
    const timer=setTimeout(()=>engine.advance(),Math.max(3800,step.text.length*130));
    return ()=>clearTimeout(timer);
  },[automatic,state.paused,state.status,state.index,step.text,engine,travel,pickup]);
  useEffect(()=>{
    const handler=(event:KeyboardEvent)=>{
      if(event.code!=='Space'||event.repeat||modal||pickup||travel||['BUTTON','INPUT','SELECT','TEXTAREA'].includes((event.target as HTMLElement)?.tagName))return;
      event.preventDefault();audio.play('sfx-page');engine.advance();
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
  // The reader's own freeze of the stage. An open panel also pauses the performance,
  // but that is not a button state and must not light the button up.
  const stagePaused=engine.stagePaused;
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
      <select className="chapter-select" aria-label="选择剧情段落" value={step.chapter} onChange={e=>{const chapter=chapters.find(c=>c.id===e.target.value)!;setAutomatic(false);setTravel(null);engine.seek(chapter.start);}}>{[1,2,3,4].map(book=><optgroup label={bookNames[book]} key={book}>{chapters.filter(c=>c.book===book).map(c=><option value={c.id} key={c.id}>{bookNames[book]} · {c.title}</option>)}</optgroup>)}</select>
      <span className="reading-progress" title={`${state.index+1} / ${story.length}`}>{progress}%<progress max="100" value={progress} aria-label="前四回剧情进度"/></span>
      <nav className="playback-controls" aria-label="演出控制">
        {/* One switch, not three. It reads 自动 while the story is waiting for the reader
            and 暂停 while the story is running itself -- the label always names what the
            button will do next, so it can never sit there looking live and do nothing. */}
        <button className={automatic?'text-button selected':'text-button'} aria-pressed={automatic}
          onClick={()=>{
            // Turning auto-play on releases a frozen stage, otherwise the button would
            // read 暂停 while the story stood still. Turning it off leaves the stage
            // exactly as the reader left it. The engine is touched outside the state
            // updater: React runs updater functions during the render, and an engine
            // that emits there would update this very component mid-render.
            const next=!automatic;
            setAutomatic(next);
            if(next)engine.pause(false);
          }}
          disabled={state.status==='error'}>
          <Icon name={automatic?'pause':'play'}/>{automatic?'暂停':'自动'}
        </button>
        <button className="text-button" onClick={()=>setModal('history')}><Icon name="book"/>回看</button>
        {/* The ledger is the reader's backpack: one tap from the header, straight to the
            balance tab, instead of three layers down through settings and the atlas. */}
        <button className="text-button" onClick={()=>{setAtlasTab('ledger');setModal('atlas');}}><Icon name="bag"/>背包</button>
        <button className="icon-button" aria-label={muted?'开启声音':'关闭声音'} aria-pressed={muted}
          onClick={()=>{const next=!muted;setMuted(next);audio.setMuted(next);}}>
          <Icon name={muted?'mute':'sound'}/>
        </button>
        {ended?<button className="next-button" onClick={restart}>再走一回 <Icon name="reset"/></button>:inMotion?<button className="next-button secondary" disabled={state.paused} onClick={()=>{if(travel)setTravel(null);else engine.skip();}}>跳过移动 <Icon name="chevron"/></button>:<button className="next-button" disabled={state.paused||state.status==='error'} onClick={()=>{audio.play('sfx-page');engine.advance();}}>继续剧情 <Icon name="arrow"/></button>}
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
          {/* Books 3–4 take place inside the estate, so their overview tab opens the
              estate map; books 1–2 happen in Yangzhou before the family is reached,
              and get the ordered trail of that book's stages instead. */}
          {overview&&(step.source.chapter<3)?<JourneyMap chapter={step.source.chapter} sceneId={state.sceneId} onVisit={node=>{setOverview(false);setAutomatic(false);engine.seek(node);}}/>:(overview||travel)&&<WorldMap sceneId={worldId} travel={travel} onVisit={id=>{const place=worldLocations.find(l=>l.id===id);const scene=place?.scene??id;const target=place?.start?story.find(s=>s.id===place.start):story.find(s=>s.source.chapter===step.source.chapter&&s.scene===scene)??story.find(s=>s.source.chapter===3&&s.scene===scene);if(target){setTravel(null);setOverview(false);setAutomatic(false);engine.seek(target.id);}}}/>}
          <div className="map-navigation">
            <div className="view-switch" aria-label="地图视图"><button aria-pressed={!overview&&!travel} onClick={()=>{setTravel(null);setOverview(false);}}>当前场景</button><button aria-pressed={overview||!!travel} onClick={()=>setOverview(true)}>{step.source.chapter<3?'本回行迹':'荣国府总览'}</button></div>
            <span className="current-place">{travel?`${worldLocations.find(l=>l.id===travel.from)?.name} → ${worldLocations.find(l=>l.id===travel.to)?.name}`:step.place}</span>
          </div>
          {/* The freeze control stays available in every view, because the walk between
              two places on the estate map is a performance too and it needs the same
              brake as the stage underneath it. */}
          <div className="map-tools" onPointerDown={e=>e.stopPropagation()}>
            {!overview&&!travel&&<button title="缩小" aria-label="缩小地图" onClick={()=>sceneRef.current?.zoom(-.15)}>−</button>}
            {!overview&&!travel&&<button title="回到剧情" aria-label="回到剧情镜头" onClick={()=>sceneRef.current?.recenter()}><Icon name="compass"/></button>}
            {!overview&&!travel&&<button title="放大" aria-label="放大地图" onClick={()=>sceneRef.current?.zoom(.15)}>＋</button>}
            <button title={stagePaused?'继续演出':'暂停演出'} aria-label={stagePaused?'继续演出':'暂停演出'} aria-pressed={stagePaused} onClick={()=>{const next=!stagePaused;engine.pause(next);if(next)setAutomatic(false);}}><Icon name={stagePaused?'play':'pause'}/></button>
          </div>
          {!overview&&!travel&&<span className="local-compass" aria-label="地图方位：北向右上，东向右下">北 ↗<br/>东 ↘</span>}
          {inMotion&&<div className="map-action-cue" role="status"><span className="action-orbit"/><span>{state.paused?'行动已暂停':travel?'黛玉正在地点之间移动':'跟随人物 · '+step.title}</span></div>}
          {state.paused&&<div className="paused-label"><Icon name="pause"/>演出已暂停</div>}
        </section>
        <section className={`dialogue-panel ${inMotion?'action-mode':'conversation-mode'} ${overview||travel?'stage-overview':''}`} aria-label="剧情对话" data-mode={inMotion?'action':'dialogue'} data-paused={state.paused}>
          {!inMotion&&<>
            <div className="speaker-portrait" key={portrait}><Portrait actor={portrait} face="right" emotion={emotionOf(step)} sad={step.mood==='sad'}/><span className="portrait-role">{step.speaker==='narrator'?'故事视角':'讲话人'}</span></div>
            {listener&&<div className="listener-portraits" aria-label="在场人物立绘">
              <div className="listener-stack" aria-hidden="true">{listeners.filter(id=>id!==listener).slice(0,2).map(id=><div key={id}><Portrait actor={id} face="left" closeup/></div>)}</div>
              <button className="listener-feature" onClick={()=>setModal(listener)} aria-label={`查看${cast[listener].fullName}资料`}><Portrait actor={listener} face="left"/><span>{cast[listener].name}</span></button>
              <div className="listener-picker" aria-label="切换在场立绘">{listeners.map((id,i)=><button key={id} className={listener===id?'active':''} onClick={()=>setListenerOffset(i)} aria-label={`显示${cast[id].fullName}立绘`} aria-pressed={listener===id}>{cast[id].name}</button>)}</div>
            </div>}
          </>}
          <div className="dialogue-body">
            <div className="speaker-line"><span className="speaker-rule"/><h2>{inMotion?'行 动':step.speaker==='narrator'?'旁白':cast[step.speaker].fullName}</h2><span className="dialogue-type">{inMotion?'地图演出':step.offscreen?'画外':step.speaker==='narrator'?'叙事':'对白'}</span>{step.source.layer&&step.source.layer!=='present'&&<span className="narrative-layer">{({dream:'梦境',recollection:'回忆',reported:'转述'} as Record<string,string>)[step.source.layer]}</span>}<span className="node-label">{state.index===story.length-1?'终幕':step.id}</span></div>
            {inMotion?<div className="action-presentation" aria-live="polite"><div className="action-path-motif"><i/><i/><i/><Icon name="compass"/></div><div><strong>{travel?'穿院而行':step.title}</strong><p>{travel?'黛玉正在两处之间赶路，稍候即至':state.paused?'演出暂停中':actionNarration(engine)}</p></div><span className="action-direction">视线回到地图 ↑</span></div>:<p className="dialogue-text" aria-live="polite">{step.text}</p>}
            {state.status==='error'&&<p className="error-message" role="alert">{state.error}</p>}
          </div>
        </section>
    </div>
    {notice&&<div className="toast" role="status">{notice}</div>}
    {pickup&&<div className="pickup-overlay" role="dialog" aria-modal="true" aria-label="获得物品">
      <section className="pickup-card">
        <header className="pickup-header"><span className="pickup-title">获得</span><small>{bookNames[pickup[0].book]??`第${pickup[0].book}回`} · {pickup.length} 件</small></header>
        <div className="pickup-goods">
          {pickup.map(entry=><article key={entry.id} className="pickup-item">
            {entry.art&&<img src={entry.art} alt={entry.what}/>}
            <div className="pickup-info">
              <strong>{entry.what}</strong>
              <span className={`ledger-mode ${entry.mode}`}>{modeNames[entry.mode]}</span>
              <small className="pickup-flow">{entry.from} → {entry.to}{entry.amount!=null?` · ${entry.amount} 两`:''}</small>
              <p>{entry.circumstance}</p>
            </div>
          </article>)}
        </div>
        <div className="pickup-actions">
          <button className="text-button" onClick={()=>{takePickup();setAtlasTab('ledger');setModal('atlas');}}>收下并打开背包</button>
          <button className="next-button pickup-confirm" onClick={takePickup} autoFocus>收下</button>
        </div>
      </section>
    </div>}
    <dialog ref={dialog} onCancel={event=>{event.preventDefault();setModal(null);}} onClick={event=>{if(event.target===dialog.current)setModal(null);}}>
      <div className="modal-header"><h2>{modal==='history'?'对白回看':modal==='settings'?'阅读设置':modal==='source'?'原文与改编':modal==='atlas'?'前四回 · 册页':modal==='cast'?'前四回 · 人物图鉴':character?.fullName}</h2><button className="icon-button" aria-label="关闭弹窗" onClick={()=>setModal(null)}><Icon name="close"/></button></div>
      {modal==='history'&&<div className="history-list">{engine.readHistory().map(entry=><article key={entry.id}><span>{entry.speaker}<small>{entry.id}</small></span><p>{entry.text}</p><button className="text-button" onClick={()=>{setModal(null);setAutomatic(false);engine.seek(entry.id);}}><Icon name="reset"/>回到此处</button></article>)}</div>}
      {modal==='settings'&&<div className="settings-body"><p>{storageError||savedLabel}</p><div className="save-actions"><button className="text-button" onClick={save} disabled={inMotion}>保存</button><button className="text-button" onClick={()=>{setModal(null);load();}}>读取</button><button className="text-button" onClick={()=>{setModal(null);restart();}}>重玩</button><button className="text-button" onClick={()=>setModal('source')}>原文与改编</button><button className="text-button" onClick={()=>setModal('atlas')}>册页</button><button className="text-button" onClick={()=>setModal('cast')}>人物图鉴</button></div><label>人物行走速度<select value={state.speed} onChange={e=>engine.setSpeed(Number(e.target.value))}><option value="0.5">慢行 · 0.5 倍</option><option value="1">常速 · 1 倍</option><option value="2">快行 · 2 倍</option></select></label><label className="check-label"><input type="checkbox" checked={showGuides} onChange={e=>{setShowGuides(e.target.checked);sceneRef.current?.guides(e.target.checked);}}/>显示地图上的引导路线</label><div className="audio-settings"><span className="audio-settings-title">声音</span><label className="check-label"><input type="checkbox" checked={!muted} onChange={e=>{const on=e.target.checked;setMuted(!on);audio.setMuted(!on);}}/>开启全部声音</label><label>背景音乐<input type="range" min="0" max="100" disabled={muted} value={Math.round(audioPrefs.bgm*100)} onChange={e=>{const v=Number(e.target.value)/100;setAudioPrefs(p=>({...p,bgm:v}));audio.setPrefs({bgm:v});}}/></label><label>音效<input type="range" min="0" max="100" disabled={muted} value={Math.round(audioPrefs.sfx*100)} onChange={e=>{const v=Number(e.target.value)/100;setAudioPrefs(p=>({...p,sfx:v}));audio.setPrefs({sfx:v});}}/></label><p className="audio-hint">关掉总开关后音乐与音效同时静默，两个滑杆仍记住原来的音量；重新打开即恢复。音乐随场景变换：园林、街市、运河、夜、室内、太虚各一曲，每一回另有专属的底乐。首次点击页面后开始播放。</p></div><p>打开设置、人物信息或对白记录时，演出会暂停；关掉弹窗后继续。标题栏的「自动」按钮同时管着自动播放：点它开始自动往下读，再点它停下来。</p><p>进度在每条对白到达后自动保存，刷新页面会恢复。隐私浏览或存储限制可能使保存失败。</p></div>}
      {modal==='source'&&<div className="source-body"><span className="source-badge">{bookNames[step.source.chapter]} · 完整剧情改编</span><p>前四回覆盖石头来历、绛珠还泪、甄家兴衰、雨村仕途、冷子兴演说、黛玉入府全程，以及第四回雨村判案、薛家入京住进梨香院。第四回 112 个节点已全部接入：应天府大堂与退堂密室、薛家入京路上、荣禧堂接风、梨香院安顿。梦境、回忆和转述均另作标识，人物不会因此出现在当下场景。</p><p>底本参考维基文库《红楼梦》第一至四回，正文已存入项目资料。除诗词和少量短句，页面文字为便于交互阅读的改写；空间布局、尺度与演出为设计补充。</p><p>当前节点：{step.id}；对应原文段落起句：“{step.source.paragraphLead}”。</p><p>地图均为 40×40 等距舞台。总览以列增为东、行增为南；西角门按西墙方案布置，黑油大门开在南墙偏东。西角门具体墙面是设计选择，原文明确的是去程出西角门、往东过正门、入黑油大门的顺序；回程门名未明示，本版选择由正门进入。原文中仅被提及、没有实际到访的地点不安排人物进入；第三回宝玉庙里还愿与贾政斋戒只作叙述。</p><p>美术由本地 ComfyUI 生成，经抠图与定位校准接入。服饰与建筑为原创视觉演绎，有形出场的人物均配有立绘与 Q 版图像；只在谈话中提及的家族成员保留为转述。</p></div>}
      {modal==='atlas'&&<div className="atlas-body">
        <div className="atlas-tabs" role="tablist" aria-label="册页视图">
          <button role="tab" aria-selected={atlasTab==='maps'} onClick={()=>setAtlasTab('maps')}>地图</button>
          <button role="tab" aria-selected={atlasTab==='cards'} onClick={()=>setAtlasTab('cards')}>见闻 · {unlocked.size}/{cards.length}</button>
          <button role="tab" aria-selected={atlasTab==='ledger'} onClick={()=>setAtlasTab('ledger')}>账簿 · {ledgerUnlocked.size}/{ledgerEntries.length}</button>
        </div>
        {atlasTab==='maps'?<>          {Object.values(engine.maps).map(map=><article key={map.id}><h3>{map.title}</h3><p>{map.labels.length?map.labels.map(l=>l.text).join(' · '):'西角门 · 换轿处 · 垂花门 · 穿堂插屏 · 贾母正房 · 后房门'}</p><small>40×40 格 · {Object.keys(map.anchors).length} 个剧情地点</small></article>)}
          <p className="atlas-note">金陵应天府、还愿庙宇、斋戒处为叙述提及，不是本回黛玉实际到访的场景。</p>
        </>:atlasTab==='cards'?<>
          <p className="atlas-note">地志卡随剧情读到即收入；金句卡在读到对应段落时入册；信物只在原文写明「交到手上」那一刻入册。收集的反馈都在这里，阅读时不会弹出打扰。</p>
          {tokens.length>0&&<section className="card-book">
            <h3 className="card-book-title">信物</h3>
            <div className="card-gallery pair">
              {tokens.map(card=>{
                const got=unlocked.has(card.id);
                return <article key={card.id} className={`card-item token ${got?'unlocked':'locked'}`} aria-label={got?card.name:'未解锁的信物'}>
                  {got&&card.image&&<img className="card-art" src={card.image} alt={card.name}/>}
                  <div className="card-face">
                    {got?<>
                      <strong className="card-name">{card.name}</strong>
                      {card.quote&&<p className="card-scroll">{card.quote.split('\n').map((line,i)=><span key={i}>{line}</span>)}</p>}
                      <small className="card-subtitle">{card.subtitle}</small>
                      <span className="card-seal">{card.attribution}</span>
                    </>:<span className="card-mark">？</span>}
                  </div>
                  <footer>{got?<><strong>{card.name}</strong><small>信物{card.source&&<span className="card-source">· 原文：{card.source}</span>}</small></>:<strong>？？？？</strong>}</footer>
                </article>;
              })}
            </div>
          </section>}
          {bonds.length>0&&<section className="card-book">
            <h3 className="card-book-title">归属</h3>
            <p className="atlas-note">那个年代，人也可以是「给」的。卡上标出这个人从哪里来、到了谁那里去，以及是赏给、买卖还是被夺。</p>
            <div className="card-gallery pair">
              {bonds.map(card=>{
                const got=unlocked.has(card.id);
                const bond=card.bond!;
                return <article key={card.id} className={`card-item bond ${got?'unlocked':'locked'}`} aria-label={got?`${card.name}的归属`:'未解锁的归属卡'}>
                  {got&&card.image&&<img className="card-art" src={card.image} alt={card.name}/>}
                  <div className="card-face">
                    {got?<>
                      <span className={`bond-mode ${bond.mode}`}>{({granted:'赏给',sold:'买卖',taken:'被夺'})[bond.mode]}</span>
                      <div className="bond-row">
                        <span className="bond-side">{bond.from}</span>
                        <span className="bond-arrow" aria-hidden="true">→</span>
                        <span className="bond-side">{bond.to}</span>
                      </div>
                      <p className="bond-note">{bond.note}</p>
                      <span className="card-seal">{bookNames[card.book]??`第${card.book}回`}</span>
                    </>:<span className="card-mark">？</span>}
                  </div>
                  <footer>{got?<><strong>{card.name}</strong><small>{card.subtitle}</small></>:<strong>？？？？</strong>}</footer>
                </article>;
              })}
            </div>
          </section>}
          {[...cardsByBook().entries()].map(([book,list])=><section key={book} className="card-book">
            <h3 className="card-book-title">{bookNames[book]??`第${book}回`}</h3>
            <div className="card-gallery">
              {list.map(card=>{
                const got=unlocked.has(card.id);
                return <article key={card.id} className={`card-item ${card.kind} ${got?'unlocked':'locked'}`} aria-label={got?card.name:'未解锁的卡片'}>
                  {got&&card.image&&<img className="card-art" src={card.image} alt={card.name}/>}
                  <div className="card-face">
                    {got?(card.kind==='line'
                      ?<><p className="card-quote">{card.quote}</p><span className="card-seal">{card.attribution}</span></>
                      :<><strong className="card-name">{card.name}</strong><small className="card-subtitle">{card.subtitle}</small><span className="card-seal">{bookNames[card.book]??`第${card.book}回`}</span></>)
                      :<span className="card-mark">？</span>}
                  </div>
                  <footer>{got?<><strong>{card.name}</strong><small>{card.kind==='line'?'金句卡':'地志卡'}</small></>:<strong>？？？？</strong>}</footer>
                </article>;
              })}
            </div>
          </section>)}
        </>:<>
          <p className="atlas-note">银两、衣物、物件、人：凡原文写明的「获得」与「给出」，都在这本账上——谁在赚钱，谁在花钱，什么东西在什么情形下、以什么价钱在谁手里转了一道。读到对应剧情，这一笔才入账。</p>
          <div className="ledger-switch" role="tablist" aria-label="账簿视角">
            <button role="tab" aria-selected={ledgerView==='people'} onClick={()=>setLedgerView('people')}>按人 · 谁赚谁花</button>
            <button role="tab" aria-selected={ledgerView==='items'} onClick={()=>setLedgerView('items')}>按物 · 流转去向</button>
          </div>
          {ledgerView==='people'?<>
          <div className="ledger-people" role="listbox" aria-label="有账目的人物">
            {ledgerPeople.map(p=>{
              const n=p.got.length+p.given.length;
              return <button key={p.name} role="option" aria-selected={ledgerPerson===p.name} className={ledgerPerson===p.name?'active':''} onClick={()=>setLedgerPerson(ledgerPerson===p.name?null:p.name)}>
                <strong>{p.name}</strong>
                <small>{n} 笔{p.net!==0?` · ${p.net>0?'赚':'花'} ${Math.abs(p.net)} 两`:''}</small>
              </button>;
            })}
          </div>
          {personBook?<>
            <p className="ledger-summary">{personBook.name}：得 {personBook.got.length} 笔 · 出 {personBook.given.length} 笔{personBook.pricedIn>0?` · 入 ${personBook.pricedIn} 两`:''}{personBook.pricedOut>0?` · 支 ${personBook.pricedOut} 两`:''}{personBook.net!==0?` · 净${personBook.net>0?'赚':'花'} ${Math.abs(personBook.net)} 两`:' · 未写价的账不计净额'}</p>
            <section className="ledger-book"><h3 className="card-book-title">得到</h3>
              {personBook.got.map(({entry})=><LedgerRow key={entry.id} entry={entry} got={ledgerUnlocked.has(entry.id)} label={`${entry.from} → ${personBook.name}`}/>)}
            </section>
            <section className="ledger-book"><h3 className="card-book-title">给出</h3>
              {personBook.given.map(({entry})=><LedgerRow key={entry.id} entry={entry} got={ledgerUnlocked.has(entry.id)} label={`${personBook.name} → ${entry.to}`}/>)}
            </section>
          </>:<section className="ledger-book"><h3 className="card-book-title">全部流转 · 按剧情先后</h3>
            {ledgerEntries.map(entry=><LedgerRow key={entry.id} entry={entry} got={ledgerUnlocked.has(entry.id)} label={`${entry.from} → ${entry.to}`}/>)}
          </section>}
          </>:<>
          <p className="atlas-note">挑一样东西，看它从哪里来、经过谁的手、最后落在谁那里——什么时候、哪一回、什么情形、价格几何。在这个年代，人在账上也是被转手的一方。</p>
          <div className="ledger-people" role="listbox" aria-label="账上的物品">
            {ledgerItems.map(t=>{
              const got=t.entries.filter(e=>ledgerUnlocked.has(e.id)).length;
              return <button key={t.key} role="option" aria-selected={ledgerItem===t.key} className={ledgerItem===t.key?'active':''} onClick={()=>setLedgerItem(ledgerItem===t.key?null:t.key)}>
                <strong>{t.label}</strong>
                <small>{categoryNames[t.category]} · {got}/{t.entries.length} 笔</small>
              </button>;
            })}
          </div>
          {itemBook&&<section className="ledger-book">
            <h3 className="card-book-title">{itemBook.label}的流转链 · 共 {itemBook.entries.length} 笔</h3>
            {itemBook.entries.map(entry=><LedgerRow key={entry.id} entry={entry} got={ledgerUnlocked.has(entry.id)} label={`${entry.from} → ${entry.to}`}/>)}
            {itemBook.entries.some(e=>e.art&&ledgerUnlocked.has(e.id))&&
              <img className="ledger-art" src={itemBook.entries.find(e=>e.art&&ledgerUnlocked.has(e.id))!.art} alt={`${itemBook.label}的货品图`}/>}
          </section>}
          </>}
        </>}
      </div>}

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
