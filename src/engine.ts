import { cellKey, findPath } from './model.ts';
import type { MapData, Point } from './model.ts';
import { story, chapter3Story, cast } from './story.ts';
import type { ActorId, Action, Move, StoryStep } from './story.ts';

export type ActorState = Point & { visible: boolean; moving: boolean; direction: number };
export type HistoryEntry = {id: string; speaker: string; text: string};
export type StoryState = {
  sceneId:string; effect:{actor:ActorId;kind:'jade'|'greet'|'rest';elapsed:number;duration:number}|null;
  index: number; status: 'moving'|'reading'|'ended'|'error'; paused: boolean;
  actors: Record<ActorId, ActorState>; roofVisible: boolean;
  focus: string; history: HistoryEntry[]; error: string | null; speed: number;
};
type Job = {actor: ActorId; path: Point[]; cursor: number};
export type SaveData = {version: 3; chapter: 'first-three'; node: string; state: StoryState};
export const SAVE_KEY = 'honglou-first-three:v3';
export const LEGACY_SAVE_KEY='honglou-chapter03:v2';

export class StoryEngine {
  maps:Record<string,MapData>;
  get map(){return this.maps[this.state.sceneId];}
  steps: StoryStep[];
  private state: StoryState;
  private listeners = new Set<() => void>();
  private jobs: Job[] = [];
  private actionIndex = 0;
  private userPaused = false;
  private overlayPaused = false;

  constructor(maps: Record<string,MapData>|MapData, steps = story) {
    this.maps=typeof (maps as MapData).id==='string' ? {[(maps as MapData).id]:maps as MapData}:maps as Record<string,MapData>; this.steps = steps;
    this.state = this.initial();
    this.enter(0);
  }
  private initial(): StoryState {
    const actors = {} as Record<ActorId, ActorState>;
    for (const id of Object.keys(cast) as ActorId[]) actors[id] = {col:13,row:28,visible:false,moving:false,direction:1};
    return {sceneId:this.steps[0].scene,effect:null,index:0,status:'moving',paused:false,actors,roofVisible:true,focus:this.steps[0].focus,history:[],error:null,speed:1};
  }
  subscribe = (listener: () => void) => { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; };
  getSnapshot = () => this.state;
  /** Remaining A* path for presentation only; does not alter movement state. */
  movementPaths() {return this.jobs.map(job=>({actor:job.actor,points:[{col:this.state.actors[job.actor].col,row:this.state.actors[job.actor].row},...job.path.slice(job.cursor).map(point=>({...point}))]}));}
  get step() { return this.steps[this.state.index]; }
  private emit() { this.state = structuredClone(this.state); for (const listener of this.listeners) listener(); }
  private anchor(name: string) { const p = this.map.anchors[name]; if (!p) throw new Error(`地点不存在：${name}`); return p; }
  private fail(error: unknown) {
    this.jobs = []; this.state.status = 'error';
    this.state.error = `[${this.step?.id ?? 'unknown'}] ${error instanceof Error ? error.message : String(error)}`;
    this.emit();
  }
  private enter(index: number) {
    try {
      this.state.index=index; this.actionIndex=0; this.jobs=[]; this.state.status='moving';
      this.state.effect=null;
      if(!this.maps[this.step.scene])throw new Error(`场景不存在：${this.step.scene}`);
      if(this.state.sceneId!==this.step.scene){this.state.sceneId=this.step.scene;this.state.roofVisible=true;for(const actor of Object.values(this.state.actors)){actor.visible=false;actor.moving=false;}}
      this.anchor(this.step.focus); this.state.focus=this.step.focus;
      this.pump(false);
    } catch (e) { this.fail(e); }
  }
  private makeJob(action: Move): Job {
    const actor = this.state.actors[action.actor];
    if (!actor?.visible) throw new Error(`移动角色未显示：${action.actor}`);
    let from: Point = actor;
    const path: Point[] = [{col:actor.col,row:actor.row}];
    for (const name of action.via) {
      const to = this.anchor(name), leg = findPath(this.map, from, to);
      path.push(...leg.slice(1)); from=to;
    }
    actor.moving=path.length>1;
    return {actor:action.actor,path,cursor:1};
  }
  private execute(action: Action, instant: boolean) {
    if (action.type === 'effect') {if(!instant)this.state.effect={actor:action.actor,kind:action.kind,elapsed:0,duration:action.duration};return;}
    if (action.type === 'roof') {this.state.roofVisible=action.visible; return;}
    if (action.type === 'show') {
      const p = this.anchor(action.at);
      if (!this.map.walkable.has(cellKey(p.col,p.row))) throw new Error(`显示地点不可通行：${action.at}`);
      Object.assign(this.state.actors[action.actor],p,{visible:true,moving:false}); return;
    }
    if (action.type === 'hide') {this.state.actors[action.actor].visible=false; return;}
    const moves = action.type==='parallel' ? action.moves : [action];
    if (new Set(moves.map(m=>m.actor)).size !== moves.length) throw new Error('同一角色不能同时移动两次');
    const jobs = moves.map(move=>this.makeJob(move));
    if (instant) {
      for (const j of jobs) Object.assign(this.state.actors[j.actor], j.path.at(-1), {moving:false});
    } else this.jobs=jobs.filter(j=>j.path.length>1);
  }
  private pump(instant: boolean) {
    while (this.actionIndex<this.step.actions.length) {
      this.execute(this.step.actions[this.actionIndex++],instant);
      if (this.jobs.length || this.state.effect) {this.emit(); return;}
    }
    this.state.status=this.state.index===this.steps.length-1 ? 'ended' : 'reading';
    if (!this.state.history.some(h=>h.id===this.step.id)) this.state.history.push({id:this.step.id,speaker:this.step.speaker==='narrator'?'旁白':cast[this.step.speaker].fullName,text:this.step.text});
    this.emit();
  }
  advance() {
    if (this.state.paused || this.state.status!=='reading') return;
    if (this.state.index+1<this.steps.length) this.enter(this.state.index+1);
  }
  tick(seconds: number) {
    if (this.state.paused || this.state.status!=='moving') return;
    if(this.state.effect){this.state.effect.elapsed+=Math.min(Math.max(seconds,0),.1);if(this.state.effect.elapsed>=this.state.effect.duration){this.state.effect=null;this.pump(false);}else this.emit();return;}
    if(!this.jobs.length)return;
    try {
      for (const job of this.jobs) {
        const actor=this.state.actors[job.actor];
        let remaining=Math.min(Math.max(seconds,0),.1)*3.8*this.state.speed;
        while (remaining>0 && job.cursor<job.path.length) {
          const to=job.path[job.cursor], dc=to.col-actor.col, dr=to.row-actor.row, length=Math.hypot(dc,dr);
          actor.direction=dc-dr>=0 ? 1 : -1;
          if (length<=remaining) {actor.col=to.col; actor.row=to.row; remaining-=length; job.cursor++;}
          else {actor.col+=dc/length*remaining; actor.row+=dr/length*remaining; remaining=0;}
        }
        actor.moving=job.cursor<job.path.length;
      }
      this.jobs=this.jobs.filter(j=>this.state.actors[j.actor].moving);
      if (!this.jobs.length) this.pump(false); else this.emit();
    } catch (e) {this.fail(e);}
  }
  skip() {
    if (this.state.paused || this.state.status!=='moving') return;
    try {
      for (const job of this.jobs) Object.assign(this.state.actors[job.actor],job.path.at(-1),{moving:false});
      this.jobs=[]; this.state.effect=null;this.pump(true);
    } catch (e) {this.fail(e);}
  }
  pause(value: boolean) {this.userPaused=value; this.updatePause();}
  overlay(value: boolean) {this.overlayPaused=value; this.updatePause();}
  private updatePause() {this.state.paused=this.userPaused||this.overlayPaused; this.emit();}
  setSpeed(value: number) {if ([.5,1,2].includes(value)) {this.state.speed=value; this.emit();}}
  seek(nodeId:string) {
    const index=this.steps.findIndex(step=>step.id===nodeId);if(index<0)throw new Error('章节不存在');
    const replay=new StoryEngine(this.maps,this.steps);
    while(replay.getSnapshot().index<index){replay.skip();if(replay.getSnapshot().status==='error')throw new Error(replay.getSnapshot().error!);replay.advance();}
    replay.skip();if(replay.getSnapshot().status==='error')throw new Error(replay.getSnapshot().error!);
    this.jobs=[];this.userPaused=false;this.overlayPaused=false;this.actionIndex=this.steps[index].actions.length;this.state=structuredClone(replay.getSnapshot());this.emit();
  }
  restart() {this.jobs=[]; this.userPaused=false; this.overlayPaused=false; this.state=this.initial(); this.enter(0);}
  serialize(): SaveData {
    if (!['reading','ended'].includes(this.state.status)) throw new Error('请等待本段移动结束后保存');
    const state=structuredClone(this.state); state.paused=false;
    return {version:3,chapter:'first-three',node:this.step.id,state};
  }
  restore(input: unknown) {
    // Validate everything before replacing the live world; malformed saves cannot corrupt it.
    const data=structuredClone(input) as {version?:number;chapter?:string;node?:string;state?:StoryState}|null;
    const legacy=data?.version===2&&data.chapter==='chapter03';
    if (!data || (!legacy&&(data.version!==3 || data.chapter!=='first-three')) || !data.state) throw new Error('存档版本不兼容');
    const state=data.state, index=this.steps.findIndex(s=>s.id===data.node);
    if (index<0 || (legacy?chapter3Story.findIndex(s=>s.id===data.node):index)!==state.index || !['reading','ended'].includes(state.status)) throw new Error('存档剧情节点无效');
    if ((index===this.steps.length-1)!==(state.status==='ended')) throw new Error('存档结束状态无效');
    if (!Array.isArray(state.history) || !state.history.every(h=>h && typeof h.id==='string' && typeof h.text==='string' && typeof h.speaker==='string')) throw new Error('存档记录无效');
    const map=this.maps[state.sceneId];
    if(!map || state.sceneId!==this.steps[index].scene || state.effect!==null)throw new Error('存档场景无效');
    if (!map.anchors[state.focus] || typeof state.roofVisible!=='boolean' || ![.5,1,2].includes(state.speed)) throw new Error('存档场景无效');
    for (const id of Object.keys(cast) as ActorId[]) {
      if(legacy&&state.actors&&!state.actors[id]&&['shiyin','fengshi','yinglian','jiaoxing','fengsu','monk','taoist','kongkong','huoqi','oldmonk'].includes(id))state.actors[id]={col:13,row:28,visible:false,moving:false,direction:1};
      const a=state.actors?.[id];
      if (!a || !Number.isInteger(a.col) || !Number.isInteger(a.row) || typeof a.visible!=='boolean' || a.moving!==false || ![-1,1].includes(a.direction)) throw new Error(`存档人物无效：${id}`);
      if (a.visible && !map.walkable.has(cellKey(a.col,a.row))) throw new Error(`存档人物位置不可通行：${id}`);
    }
    this.jobs=[]; this.actionIndex=this.steps[index].actions.length; this.userPaused=false; this.overlayPaused=false;
    this.state=structuredClone(state); this.state.index=index;this.state.paused=false; this.state.error=null; this.emit();
  }
}
