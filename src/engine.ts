import { cellKey, findPath, nearestFreeCell } from './model.ts';
import type { MapData, Point } from './model.ts';
import { stagedStory, chapter3Story, cast } from './story.ts';
import type { ActorId, Action, Move, StoryStep } from './story.ts';

export type ActorState = Point & { visible: boolean; moving: boolean; direction: number };
export type HistoryEntry = {id: string; speaker: string; text: string};
export type StoryState = {
  sceneId:string; effect:{actor:ActorId;kind:'jade'|'greet'|'rest';elapsed:number;duration:number}|null;
  index: number; status: 'moving'|'reading'|'ended'|'error'; paused: boolean;
  actors: Record<ActorId, ActorState>; roofVisible: boolean;
  focus: string; history: HistoryEntry[]; error: string | null; speed: number;
  /** Every line reached so far, kept across a jump so the log of what has been read is
   *  not cut short when the reader goes back to look at an earlier passage. */
  readLog?: string[];
};
type Job = {actor: ActorId; path: Point[]; cursor: number};
/** v4 adds chapter four at the end of the line, so an old finale is no longer the finale. */
export type SaveData = {version: 4; chapter: 'four'; node: string; state: StoryState};
export const SAVE_KEY = 'honglou-four-chapters:v4';
export const LEGACY_SAVE_KEY='honglou-first-three:v3';
export const LEGACY_V2_KEY='honglou-chapter03:v2';

export class StoryEngine {
  maps:Record<string,MapData>;
  get map(){return this.maps[this.state.sceneId];}
  steps: StoryStep[];
  private state: StoryState;
  private listeners = new Set<() => void>();
  private jobs: Job[] = [];
  // The whole move batch in authored order, kept until the last walker is
  // home, so arrivals are restaged as one room and a watched walk and a
  // skipped one end in exactly the same facing.
  private arrivals: Job[] = [];
  private actionIndex = 0;
  private userPaused = false;
  private overlayPaused = false;
  // The stage the story is on has to be painted before anybody walks on it.
  // A scene swap tears the old Phaser game down and builds a new one; until the
  // new artwork exists, the walk would be staged over an empty board. The
  // renderer holds the board shut while it loads and releases it when the map
  // is up. The engine is usable without a renderer (unit tests, replays), so
  // the gate is open unless somebody explicitly locks it.
  private stageLocked = false;
  private pendingLocked = false;

  constructor(maps: Record<string,MapData>|MapData, steps = stagedStory) {
    this.maps=typeof (maps as MapData).id==='string' ? {[(maps as MapData).id]:maps as MapData}:maps as Record<string,MapData>; this.steps = steps;
    this.state = this.initial();
    this.enter(0);
  }
  private initial(): StoryState {
    const actors = {} as Record<ActorId, ActorState>;
    for (const id of Object.keys(cast) as ActorId[]) actors[id] = {col:13,row:28,visible:false,moving:false,direction:1};
    return {sceneId:this.steps[0].scene,effect:null,index:0,status:'moving',paused:false,actors,roofVisible:true,focus:this.steps[0].focus,history:[],readLog:[],error:null,speed:1};
  }
  subscribe = (listener: () => void) => { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; };
  getSnapshot = () => this.state;
  /** Hold the stage shut while its map is still loading. The renderer locks the
   *  board when a scene starts and releases it once the artwork is on screen;
   *  until then nobody moves, so a walk is never staged over an empty stage. */
  lockStage(locked: boolean) {
    this.stageLocked=locked;
    if(!locked&&this.pendingLocked){this.pendingLocked=false;this.pump(false);}
  }
  /** Whether the stage is currently held shut. Exposed for the browser tests:
   *  a walk that starts before the board is up is only observable from here. */
  get stageIsLocked() { return this.stageLocked; }
  /** Remaining A* path for presentation only; does not alter movement state. */
  movementPaths() {return this.jobs.map(job=>({actor:job.actor,points:[{col:this.state.actors[job.actor].col,row:this.state.actors[job.actor].row},...job.path.slice(job.cursor).map(point=>({...point}))]}));}
  get step() { return this.steps[this.state.index]; }
  private emit() { this.state = structuredClone(this.state); for (const listener of this.listeners) listener(); }
  private anchor(name: string) { const p = this.map.anchors[name]; if (!p) throw new Error(`地点不存在：${name}`); return p; }
  private fail(error: unknown) {
    this.jobs = []; this.arrivals = []; this.state.status = 'error';
    this.state.error = `[${this.step?.id ?? 'unknown'}] ${error instanceof Error ? error.message : String(error)}`;
    this.emit();
  }
  private enter(index: number) {
    try {
      this.state.index=index; this.actionIndex=0; this.jobs=[]; this.arrivals=[]; this.state.status='moving';
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
  /** Whoever appears somewhere — shown in or walked in — turns to face the
   *  nearest person already there, and the people already there turn to face
   *  them: a room looks at whoever just arrived, which is how a standing
   *  person is staged on the isometric board. The side follows the same
   *  screen-x convention as walking, col-row increasing being to the right. */
  private faceTheRoom(actor: ActorId, at: Point) {
    const side=(from: Point, to: Point)=>(to.col-from.col)-(to.row-from.row)>=0?1:-1;
    let nearest: ActorId|null=null, nearestD=Infinity;
    for (const [id,o] of Object.entries(this.state.actors)) {
      if (id===actor || !o.visible) continue;
      const d=Math.abs(o.col-at.col)+Math.abs(o.row-at.row);
      if (d<nearestD) { nearestD=d; nearest=id as ActorId; }
    }
    if (nearest) this.state.actors[actor].direction=side(at,this.state.actors[nearest]);
    for (const [id,o] of Object.entries(this.state.actors)) {
      if (id===actor || !o.visible) continue;
      o.direction=side(o,at);
    }
  }
  /** With nobody in the room to face, a walker keeps pointing the way the last
   *  leg of the walk went — the direction an animated walk ends with, so a
   *  skipped walk lands the same way. */
  private legFacing(job: Job) {
    const p=job.path;
    if (p.length<2) return;
    const a=p[p.length-2], b=p[p.length-1];
    this.state.actors[job.actor].direction=(b.col-a.col)-(b.row-a.row)>=0?1:-1;
  }
  /** The script sometimes stages two people on one anchor tile. Nobody can share
   *  a floor tile: the first arrival keeps the authored cell and everyone after
   *  steps to the closest free tile. `jobs` are resolved in authored order, so
   *  a watched walk and a skipped one land identically. */
  private resolveDestinations(jobs: Job[]) {
    const occupied = new Set<string>();
    for (const [id, actor] of Object.entries(this.state.actors)) {
      if (!actor.visible || jobs.some(j=>j.actor===id)) continue;
      occupied.add(cellKey(Math.round(actor.col), Math.round(actor.row)));
    }
    for (const job of jobs) {
      const actor = this.state.actors[job.actor];
      if (!actor.visible) continue;
      const dest = job.path.at(-1)!;
      const free = nearestFreeCell(this.map, dest, occupied) ?? dest;
      occupied.add(cellKey(free.col, free.row));
      if (free.col===dest.col && free.row===dest.row) continue;
      // Replace the final leg with a real walk to the free tile so an animated
      // arrival and a skipped one end on the same tile without a teleport.
      const prev = job.path.at(-2)!;
      const leg = findPath(this.map, prev, free);
      job.path = [...job.path.slice(0,-1), ...leg.slice(1)];
    }
  }
  private execute(action: Action, instant: boolean) {
    if (action.type === 'effect') {if(!instant)this.state.effect={actor:action.actor,kind:action.kind,elapsed:0,duration:action.duration};return;}
    if (action.type === 'roof') {this.state.roofVisible=action.visible; return;}
    if (action.type === 'show') {
      const p = this.anchor(action.at);
      if (!this.map.walkable.has(cellKey(p.col,p.row))) throw new Error(`显示地点不可通行：${action.at}`);
      const occupied = new Set<string>();
      for (const [id, actor] of Object.entries(this.state.actors)) {
        if (id!==action.actor && actor.visible) occupied.add(cellKey(actor.col, actor.row));
      }
      const spot = nearestFreeCell(this.map, p, occupied) ?? p;
      Object.assign(this.state.actors[action.actor],spot,{visible:true,moving:false});
      this.faceTheRoom(action.actor,spot); return;
    }
    if (action.type === 'hide') {this.state.actors[action.actor].visible=false; return;}
    const moves = action.type==='parallel' ? action.moves : [action];
    if (new Set(moves.map(m=>m.actor)).size !== moves.length) throw new Error('同一角色不能同时移动两次');
    const jobs = moves.map(move=>this.makeJob(move));
    this.resolveDestinations(jobs);
    if (instant) {
      for (const j of jobs) Object.assign(this.state.actors[j.actor], j.path.at(-1), {moving:false});
      for (const j of jobs) { this.legFacing(j); this.faceTheRoom(j.actor, this.state.actors[j.actor]); }
    } else {
      // A move to where the person already stands only turns them to the room.
      for (const j of jobs) if (j.path.length===1) this.faceTheRoom(j.actor, this.state.actors[j.actor]);
      this.jobs=jobs.filter(j=>j.path.length>1);
      this.arrivals=jobs;
    }
  }
  private pump(instant: boolean) {
    // A fresh scene waits for its board. The move that brings the reader there is
    // held back until the renderer reports the map is up, so nobody walks across
    // an empty stage. Everything else on the step is staged as authored.
    if(this.stageLocked&&!instant&&this.jobs.length===0&&this.state.effect===null){
      const next=this.step.actions[this.actionIndex];
      if(next&&(next.type==='move'||next.type==='parallel')){this.pendingLocked=true;return;}
    }
    while (this.actionIndex<this.step.actions.length) {
      this.execute(this.step.actions[this.actionIndex++],instant);
      if (this.jobs.length || this.state.effect) {this.emit(); return;}
    }
    this.state.status=this.state.index===this.steps.length-1 ? 'ended' : 'reading';
    if (!this.state.history.some(h=>h.id===this.step.id)) this.state.history.push({id:this.step.id,speaker:this.step.speaker==='narrator'?'旁白':cast[this.step.speaker].fullName,text:this.step.text});
    const log=this.state.readLog??(this.state.readLog=[]);
    if(!log.includes(this.step.id))log.push(this.step.id);
    this.emit();
  }
  advance() {
    if (this.state.paused || this.state.status!=='reading') return;
    if (this.state.index+1<this.steps.length) this.enter(this.state.index+1);
  }
  tick(seconds: number) {
    if (this.state.paused || this.state.status!=='moving') return;
    // A locked stage means the board is still being painted: nobody walks and
    // nothing plays out until the renderer releases it.
    if(this.stageLocked)return;
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
      if (!this.jobs.length) {
        // Everyone is home: restage the whole batch once, in authored order and
        // with every arrival in place, so a watched walk and a skipped one end
        // in exactly the same facing.
        for (const job of this.arrivals) { this.legFacing(job); this.faceTheRoom(job.actor, this.state.actors[job.actor]); }
        this.arrivals=[];
        this.pump(false);
      } else this.emit();
    } catch (e) {this.fail(e);}
  }
  skip() {
    if (this.state.paused || this.state.status!=='moving') return;
    // Skipping is a reader's own decision and must work even while the board is
    // still loading: it drops the walk and stages the arrival in place. It does
    // not unlock the stage — the renderer owns that, so the next walk still
    // waits for the board.
    this.pendingLocked=false;
    try {
      for (const job of this.jobs) Object.assign(this.state.actors[job.actor],job.path.at(-1),{moving:false});
      // Restage the whole batch once every arrival is in place, matching the
      // animated path above move for move.
      for (const job of this.arrivals) { this.legFacing(job); this.faceTheRoom(job.actor, this.state.actors[job.actor]); }
      this.jobs=[]; this.arrivals=[]; this.state.effect=null;this.pump(true);
    } catch (e) {this.fail(e);}
  }
  pause(value: boolean) {this.userPaused=value; this.updatePause();}
  overlay(value: boolean) {this.overlayPaused=value; this.updatePause();}
  /** Whether the reader froze the performance on purpose. The overlay (an open panel)
   *  also pauses it, but that one is not the reader's doing and must not be shown
   *  as a button state. */
  get stagePaused() {return this.userPaused;}
  private updatePause() {this.state.paused=this.userPaused||this.overlayPaused; this.emit();}
  setSpeed(value: number) {if ([.5,1,2].includes(value)) {this.state.speed=value; this.emit();}}
  seek(nodeId:string) {
    const index=this.steps.findIndex(step=>step.id===nodeId);if(index<0)throw new Error('章节不存在');
    const replay=new StoryEngine(this.maps,this.steps);
    while(replay.getSnapshot().index<index){replay.skip();if(replay.getSnapshot().status==='error')throw new Error(replay.getSnapshot().error!);replay.advance();}
    replay.skip();if(replay.getSnapshot().status==='error')throw new Error(replay.getSnapshot().error!);
    // Jumping back to an earlier line must not erase what has been read: the panel called
    // 回看 is a log of the whole reading, not only of the stretch since the last jump.
    const read=[...new Set([...(this.state.readLog??[]),...replay.getSnapshot().history.map(h=>h.id)])];
    this.jobs=[];this.arrivals=[];this.userPaused=false;this.overlayPaused=false;this.actionIndex=this.steps[index].actions.length;this.state=structuredClone(replay.getSnapshot());this.state.readLog=read;this.emit();
  }

  /** Every line the reader has reached, oldest first, with the text as it was read. */
  readHistory(): HistoryEntry[] {
    const byId=new Map<string,HistoryEntry>();
    for(const entry of this.state.history)byId.set(entry.id,entry);
    for(const id of this.state.readLog??[]){
      if(byId.has(id))continue;
      const step=this.steps.find(s=>s.id===id);
      if(!step)continue;
      byId.set(id,{id,speaker:step.speaker==='narrator'?'旁白':cast[step.speaker].fullName,text:step.text});
    }
    return [...byId.values()].sort((a,b)=>this.steps.findIndex(s=>s.id===a.id)-this.steps.findIndex(s=>s.id===b.id));
  }
  restart() {this.jobs=[]; this.arrivals=[]; this.userPaused=false; this.overlayPaused=false; this.state=this.initial(); this.enter(0);}
  serialize(): SaveData {
    if (!['reading','ended'].includes(this.state.status)) throw new Error('请等待本段移动结束后保存');
    const state=structuredClone(this.state); state.paused=false;
    return {version:4,chapter:'four',node:this.step.id,state};
  }
  restore(input: unknown) {
    // Validate everything before replacing the live world; malformed saves cannot corrupt it.
    const data=structuredClone(input) as {version?:number;chapter?:string;node?:string;state?:StoryState}|null;
    const current=data?.version===4&&data.chapter==='four';
    const recent=data?.version===3&&data.chapter==='first-three';
    const legacy=data?.version===2&&data.chapter==='chapter03';
    if (!data || (!current&&!recent&&!legacy) || !data.state) throw new Error('存档版本不兼容');
    const state=data.state, index=this.steps.findIndex(s=>s.id===data.node);
    if (index<0 || (legacy?chapter3Story.findIndex(s=>s.id===data.node):index)!==state.index || !['reading','ended'].includes(state.status)) throw new Error('存档剧情节点无效');
    // Nodes of chapter four were appended after the old finale; a save that ended there must
    // reopen as ordinary reading so the story can continue instead of pretending to be over.
    const status=(index===this.steps.length-1)!==(state.status==='ended')?'reading':state.status;
    if (index===this.steps.length-1&&status!=='ended') throw new Error('存档结束状态无效');
    if (!Array.isArray(state.history) || !state.history.every(h=>h && typeof h.id==='string' && typeof h.text==='string' && typeof h.speaker==='string')) throw new Error('存档记录无效');
    // The read log is optional in an old save; without it the log of what has been read
    // simply starts again from the lines the save itself carries.
    if(state.readLog!==undefined&&(!Array.isArray(state.readLog)||state.readLog.some(id=>typeof id!=='string')))throw new Error('存档记录无效');
    const map=this.maps[state.sceneId];
    if(!map || state.sceneId!==this.steps[index].scene || state.effect!==null)throw new Error('存档场景无效');
    if (!map.anchors[state.focus] || typeof state.roofVisible!=='boolean' || ![.5,1,2].includes(state.speed)) throw new Error('存档场景无效');
    state.actors=state.actors??{} as StoryState['actors'];
    for (const id of Object.keys(cast) as ActorId[]) {
      if(legacy&&state.actors&&!state.actors[id]&&['shiyin','fengshi','yinglian','jiaoxing','fengsu','monk','taoist','kongkong','huoqi','oldmonk'].includes(id))state.actors[id]={col:13,row:28,visible:false,moving:false,direction:1};
      // Actors added by a later chapter are missing from older saves; seed them invisible.
      if(!state.actors[id])state.actors[id]={col:13,row:28,visible:false,moving:false,direction:1};
      const a=state.actors?.[id];
      if (!a || !Number.isInteger(a.col) || !Number.isInteger(a.row) || typeof a.visible!=='boolean' || a.moving!==false || ![-1,1].includes(a.direction)) throw new Error(`存档人物无效：${id}`);
      if (a.visible && !map.walkable.has(cellKey(a.col,a.row))) throw new Error(`存档人物位置不可通行：${id}`);
    }
    this.jobs=[]; this.arrivals=[]; this.actionIndex=this.steps[index].actions.length; this.userPaused=false; this.overlayPaused=false;
    this.state=structuredClone(state); this.state.index=index; this.state.status=status; this.state.paused=false; this.state.error=null; this.emit();
  }
}
