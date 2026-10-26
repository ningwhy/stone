import { createRoot } from 'react-dom/client';
const rawMaps=import.meta.glob('../maps/*.tmj',{query:'?raw',import:'default',eager:true}) as Record<string,string>;
import { parseTiledMap } from './model.ts';
import { SAVE_KEY, LEGACY_SAVE_KEY, StoryEngine } from './engine.ts';
import { App } from './App.tsx';
import './styles.css';

const root=createRoot(document.getElementById('root')!);
try {
  const maps=Object.fromEntries(Object.values(rawMaps).map(raw=>{const map=parseTiledMap(JSON.parse(raw));return [map.id,map];}));
  const engine=new StoryEngine(maps);
  // Expose the engine so the browser tests can watch the stage gate: whether the
  // walkers move while the map of the next scene is still loading is only
  // observable from the engine's own state, not from the rendered frame.
  if (typeof window !== 'undefined') (window as unknown as {__engine?:StoryEngine}).__engine=engine;
  let notice='';
  try {
    const saved=localStorage.getItem(SAVE_KEY)??localStorage.getItem(LEGACY_SAVE_KEY);
    if(saved) {engine.restore(JSON.parse(saved));notice='已恢复上次的地图与对白进度';}
  } catch {notice='旧存档无法读取，已从第一回开篇重新开始';}
  root.render(<App engine={engine} initialNotice={notice}/>);
} catch(error) {
  root.render(<main className="startup-error"><h1>地图暂时无法载入</h1><p role="alert">{error instanceof Error?error.message:String(error)}</p><p>请检查 Tiled 地图中的 Anchors、Routes 与 PlanZones 对象层。</p></main>);
}
