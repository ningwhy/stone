import Phaser from 'phaser';
import { artAssets, artGround, artImage } from './art.ts';
import { project, zoneAt } from './model.ts';
import type { ArtObject, MapData } from './model.ts';
import { cast, paintedFacing } from './story.ts';
import type { ActorId } from './story.ts';
import type { StoryEngine } from './engine.ts';

export class MapScene extends Phaser.Scene {
  engine: StoryEngine;
  mapData: MapData;
  actorViews = new Map<ActorId, Phaser.GameObjects.Container>();
  private actorSprites = new Map<ActorId, Phaser.GameObjects.Image>();
  roof?: Phaser.GameObjects.Graphics;
  artViews: {view:Phaser.GameObjects.Image;object:ArtObject}[] = [];
  grid?: Phaser.GameObjects.Graphics;
  passageRoof?: Phaser.GameObjects.Graphics;
  routeGuide?: Phaser.GameObjects.Graphics;
  actionTrail?: Phaser.GameObjects.Graphics;
  actionHalo?: Phaser.GameObjects.Graphics;
  private actionClock = 0;
  manual = false;
  presentationPaused = false;
  private placeLabels:Phaser.GameObjects.Text[]=[];
  private actorLabels=new Map<ActorId,Phaser.GameObjects.Text>();
  onActor: (id: ActorId) => void;
  onReady?: (scene: MapScene) => void;
  onProgress?: (value: number) => void;
  private drag?: {x:number;y:number;scrollX:number;scrollY:number;moved:boolean};
  private zoomFactor = 1;
  private unsubscribe?: () => void;
  private clock = 0;
  private reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;

  constructor(engine: StoryEngine, onActor: (id: ActorId) => void) {
    super('Rongguo'); this.engine=engine; this.mapData=engine.map; this.onActor=onActor;
  }
  private p(col:number,row:number) {return project({col:col-.5,row:row-.5},this.mapData);}
  private polygon(g:Phaser.GameObjects.Graphics, points:{x:number;y:number}[], fill:number, alpha=1, stroke=0xa9a68f) {
    g.fillStyle(fill,alpha);g.lineStyle(1,stroke,.65);g.beginPath();g.moveTo(points[0].x,points[0].y);
    for (const p of points.slice(1)) g.lineTo(p.x,p.y);
    g.closePath();g.fillPath();g.strokePath();
  }
  private rect(g:Phaser.GameObjects.Graphics,c:number,r:number,w:number,h:number,color:number) {
    this.polygon(g,[this.p(c,r),this.p(c+w,r),this.p(c+w,r+h),this.p(c,r+h)],color);
  }
  preload() {
    this.load.on('progress', (value: number) => this.onProgress?.(value));
    const used=new Set(this.mapData.art.map(a=>a.asset));
    for(const step of this.engine.steps.filter(s=>s.scene===this.mapData.id))for(const action of step.actions){
      if(action.type==='show')used.add(action.actor==='sedan'?'sedan-chair':`${action.actor}-chibi`);
    }
    for(const key of used){const asset=artAssets[key];if(asset)this.load.image(key,artImage(key));}
  }
  private artwork() {
    for(const object of this.mapData.art) {
      const ground=artGround(object);
      const image=this.add.image(object.x,object.y,object.asset).setOrigin(.5,1)
        .setDisplaySize(object.width,object.height).setDepth(ground.y+object.depthOffset);
      this.artViews.push({view:image,object});
      if(object.asset==='garden-tree' || object.asset==='garden-rock') {
        const shadow=this.add.graphics().setDepth(-9990);
        shadow.fillStyle(0x68755a,.12);shadow.fillEllipse(ground.x+12,ground.y+6,object.width*.52,object.width*.18);
      }
    }
  }
  create() {
    const floor=this.add.graphics().setDepth(-10000);
    this.rect(floor,0,0,40,40,this.mapData.theme==='night'?0xc7c9c5:this.mapData.theme==='myth'?0xd4d9c7:this.mapData.theme==='dream'?0xd9e5df:this.mapData.theme==='ruins'?0xd3cbbd:0xeee8d7);
    if(this.mapData.theme==='river') {
      this.rect(floor,20,22,18,15,0xa8c5c2);
      floor.lineStyle(1,0xe1eee7,.4);
      for(let i=0;i<55;i++){const p=this.p(21+i%16,23+Math.floor(i/16)*3);floor.lineBetween(p.x,p.y,p.x+35,p.y+3);}
    }

    // Seeded paper grain, garden islands and inset paving avoid a uniform debug grid.
    let seed=102166;
    const random=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
    for(let i=0;i<3600;i++) {
      const p=this.p(random()*40,random()*40);
      floor.fillStyle(random()>.5?0x9d9576:0xffffff,.07);floor.fillCircle(p.x,p.y,random()*2.5+.5);
    }
    for(const z of this.mapData.zones) {
      if(['myth','dream','ruins'].includes(this.mapData.theme))continue;
      // Tiled marks the interior floors; older stages without the flag fall back
      // to the theme so the shipped scenes keep their look.
      const indoor=z.indoor ?? (z.id==='F'||['interior','night'].includes(this.mapData.theme));
      this.rect(floor,z.col-.18,z.row-.18,z.width+.36,z.height+.36,0xb4ac92);
      this.rect(floor,z.col,z.row,z.width,z.height,indoor?0xd5c5a5:0xe5decb);
      for(let c=z.col;c<z.col+z.width;c++)for(let r=z.row;r<z.row+z.height;r++) {
        const shade=indoor?[0xdfd0b3,0xd9c9aa,0xd6c4a2]:[0xded8c6,0xe4decd,0xe9e2d2,0xd8d3c2];
        this.rect(floor,c+.025,r+.025,.95,.95,shade[Math.floor(random()*shade.length)]);
        if(random()>.45) {
          const p=this.p(c+random(),r+random());floor.lineStyle(1,0x9d9c82,.18);
          floor.lineBetween(p.x,p.y,p.x+10+random()*18,p.y+random()*6);
        }
      }
    }
    if(this.mapData.id==='entry')for(let c=11;c<=16;c++)this.rect(floor,c,17,1,1,0xe6deca);
    for(const [c,r,w,h] of (['interior','night','street','myth','dream','ruins'].includes(this.mapData.theme)?[]:[[6,24,3,6],[6,15,3,5],[27,16,3,6],[29,5,4,4],[15,10,2,3],[24,19,4,2],[6,6,5,4]])) {
      this.rect(floor,c,r,w,h,0xbfc6a6);this.rect(floor,c+.15,r+.15,w-.3,h-.3,0xcbd0b2);
      for(let i=0;i<90;i++) {
        const p=this.p(c+random()*w,r+random()*h);floor.fillStyle(i%3?0x899779:0xf3d8ce,.38);floor.fillEllipse(p.x,p.y,3+random()*6,2);
      }
    }
    const grid=this.add.graphics().setDepth(-9998).setVisible(false);this.grid=grid;
    grid.lineStyle(1,0x847d61,.25);
    for(let i=0;i<=40;i++) {
      const a=this.p(i,0),b=this.p(i,40),c=this.p(0,i),d=this.p(40,i);
      grid.lineBetween(a.x,a.y,b.x,b.y);grid.lineBetween(c.x,c.y,d.x,d.y);
    }
    if(this.mapData.theme==='ruins'){
      for(let i=0;i<180;i++){const p=this.p(11+random()*17,10+random()*12);floor.fillStyle(i%3?0x7c7770:0x9a6551,.5);floor.fillRect(p.x,p.y,7+random()*13,3+random()*4);}
    }
    if(this.mapData.theme==='dream'){
      for(let i=0;i<70;i++){const p=this.p(random()*40,random()*40);floor.lineStyle(1,0xf5f5e4,.5);floor.strokeEllipse(p.x,p.y,20+random()*55,5+random()*10);}
    }
    if(this.mapData.id==='east'){
      const boundary=this.add.graphics().setDepth(-9900);
      for(const [left,right] of [[9,22.5],[25.5,29]]){const a=this.p(left,28.5),b=this.p(right,28.5);boundary.lineStyle(28,0xe3dac2);boundary.lineBetween(a.x,a.y-14,b.x,b.y-14);boundary.lineStyle(6,0x758573);boundary.lineBetween(a.x,a.y-30,b.x,b.y-30);}
    }
    this.artwork();
    if(this.mapData.id==='entry') {
    const boundary=this.add.graphics().setDepth(-9900);
    for(const [start,end] of [[27,31],[33,36]]){const a=this.p(3.5,start),b=this.p(3.5,end);boundary.lineStyle(28,0xe3dac2);boundary.lineBetween(a.x,a.y-14,b.x,b.y-14);boundary.lineStyle(6,0x758573);boundary.lineBetween(a.x,a.y-30,b.x,b.y-30);}
    // A low open colonnade keeps the turning route and the freestanding screen readable.
    const colonnade=this.add.graphics().setDepth(-1000);
    for(const [c,r] of [[10,18],[10,21],[10,24],[17,18],[17,21],[17,24]]) {
      const p=this.p(c,r);colonnade.fillStyle(0xa78a68);colonnade.fillEllipse(p.x,p.y,30,15);
      colonnade.fillStyle(0x915b48);colonnade.fillRect(p.x-5,p.y-78,10,78);
      colonnade.lineStyle(2,0xc79670);colonnade.lineBetween(p.x-2,p.y-75,p.x-2,p.y-3);
    }
    this.screen();this.bench(17,5);this.bench(23,5);this.bench(25,6);
    }
    const labels=this.mapData.id==='entry' ? [['flower_gate','垂花门'],['passage_exit','穿堂'],['courtyard_center','贾母院落'],['grandmother_seat','贾母正房']].map(([anchor,text])=>({text,point:this.mapData.anchors[anchor]})) : this.mapData.labels;
    for(const {text,point} of labels) {
      const p=project(point,this.mapData);
      const label=this.add.text(p.x,p.y+80,text,{fontFamily:'"Songti SC", SimSun, serif',fontSize:'13px',color:'#6c6451',backgroundColor:'#f4eddd',padding:{x:13,y:6}}).setOrigin(.5).setAlpha(.9).setDepth(5000);this.placeLabels.push(label);
    }
    const guide=this.add.graphics().setDepth(-10).setVisible(false); this.routeGuide=guide;
    const route=this.mapData.routes.arrival ?? [];
    const start=route.indexOf('flower_gate_stop');
    for (let i=Math.max(start,0)+1;i<route.length;i++) {
      const a=project(this.mapData.anchors[route[i-1]],this.mapData),b=project(this.mapData.anchors[route[i]],this.mapData);
      const distance=Math.hypot(b.x-a.x,b.y-a.y);
      guide.fillStyle(0x9b8053,.6);
      for (let at=0;at<distance;at+=24) guide.fillCircle(a.x+(b.x-a.x)*at/distance,a.y+(b.y-a.y)*at/distance,2.5);
    }
    this.actionTrail=this.add.graphics().setDepth(-4);
    this.actionHalo=this.add.graphics().setDepth(4500);
    for (const id of Object.keys(cast) as ActorId[]) this.makeActor(id);
    this.input.on('pointerdown',(pointer:Phaser.Input.Pointer)=>{if (pointer.downElement?.tagName==='CANVAS') this.drag={x:pointer.x,y:pointer.y,scrollX:this.cameras.main.scrollX,scrollY:this.cameras.main.scrollY,moved:false};});
    this.input.on('pointermove',(pointer:Phaser.Input.Pointer)=>{
      if (!this.drag || !pointer.isDown) return;
      const dx=pointer.x-this.drag.x,dy=pointer.y-this.drag.y;
      if (Math.hypot(dx,dy)>5) {this.manual=true;this.drag.moved=true;}
      if (this.drag.moved) this.cameras.main.setScroll(this.drag.scrollX-dx/this.cameras.main.zoom,this.drag.scrollY-dy/this.cameras.main.zoom);
    });
    this.input.on('pointerup',()=>{queueMicrotask(()=>{this.drag=undefined;});});
    this.input.on('wheel',(_pointer:Phaser.Input.Pointer,_objects:unknown, _dx:number,dy:number)=>this.zoom(dy>0?-.1:.1));
    this.scale.on('resize',()=>this.fit());
    this.unsubscribe=this.engine.subscribe(()=>this.sync());
    this.events.once('shutdown',()=>this.unsubscribe?.());
    this.fit();this.sync();
    const center=this.target();this.cameras.main.centerOn(center.x,center.y);
    this.onReady?.(this);
  }
  private screen() {
    const block=this.mapData.blockers[0]; if(!block)return;
    const p=this.p(block.col+1,block.row+.5),g=this.add.graphics({x:p.x,y:p.y}).setDepth(p.y);
    g.fillStyle(0x8f7758);g.fillRoundedRect(-65,-100,130,100,3);g.fillStyle(0xd7cfaa);g.fillRect(-56,-91,112,79);
    g.lineStyle(2,0xa49f77);for(let x=-24;x<50;x+=35)g.lineBetween(x,-90,x,-13);
    g.lineStyle(3,0x8a9a75);g.lineBetween(-35,-18,13,-77);g.lineBetween(13,-77,39,-36);
    g.fillStyle(0x9cab84,.7);g.fillEllipse(12,-65,28,17);g.fillEllipse(-10,-40,33,19);
  }
  private bench(c:number,r:number) {
    const p=this.p(c+.5,r+.5),g=this.add.graphics({x:p.x,y:p.y}).setDepth(p.y-10);
    g.fillStyle(0xa79574);g.fillRoundedRect(-25,-24,50,21,4);g.lineStyle(4,0x8b775a);g.lineBetween(-21,-3,-21,9);g.lineBetween(21,-3,21,9);
  }
  private makeActor(id:ActorId) {
    const actor=cast[id],container=this.add.container(0,0),g=this.add.graphics();container.add(g);
    const spriteKey=id==='sedan'?'sedan-chair':`${id}-chibi`;
    const spriteAsset=artAssets[spriteKey];
    if(spriteAsset) {
      g.fillStyle(0x546b55,.16);g.fillEllipse(0,2,id==='sedan'?110:40,16);
      const sprite=this.add.image(0,0,spriteKey).setOrigin(spriteAsset.anchor[0]/spriteAsset.width,spriteAsset.anchor[1]/spriteAsset.height);
      container.add(sprite);this.actorSprites.set(id,sprite);
    } else if(id==='sedan') {
      g.fillStyle(0xa36f5a);g.fillRoundedRect(-30,-60,60,58,5);g.fillStyle(0x7b584a);g.fillTriangle(-37,-60,37,-60,0,-85);
    } else if(id==='daiyu') {
      g.fillStyle(0x546b55,.16);g.fillEllipse(0,2,38,14);
      const asset=artAssets['daiyu-chibi'];
      const sprite=this.add.image(0,0,'daiyu-chibi').setOrigin(asset.anchor[0]/asset.width,asset.anchor[1]/asset.height);
      container.add(sprite);this.actorSprites.set(id,sprite);
    } else {
      g.fillStyle(0x546b55,.18);g.fillEllipse(0,1,39,15);
      g.fillStyle(actor.color);g.fillTriangle(-18,-9,18,-9,0,-50);g.fillRoundedRect(-13,-34,26,23,5);
      g.lineStyle(3,0xe0cda8,.9);g.lineBetween(-6,-34,5,-17);g.lineBetween(6,-34,-3,-17);
      g.fillStyle(0xeee0c7);g.fillCircle(0,-52,16);g.fillStyle(id==='grandmother'?0x8a8680:0x434d45);g.fillEllipse(0,-65,33,20);g.fillCircle(-14,-55,7);g.fillCircle(14,-55,7);
      g.fillStyle(0x465148);g.fillCircle(-5,-52,1.5);g.fillCircle(5,-52,1.5);
      g.lineStyle(1,0xb38c7a,.8);g.lineBetween(-3,-45,3,-45);
      g.fillStyle(0xe8c994);g.fillCircle(12,-68,3);
    }
    const label=this.add.text(0,16,actor.name,{fontFamily:'"PingFang SC", sans-serif',fontSize:'12px',color:'#475e51',backgroundColor:'#f4efdf',padding:{x:9,y:4}}).setOrigin(.5,0);container.add(label);this.actorLabels.set(id,label);
    container.setSize(75,110).setInteractive(new Phaser.Geom.Rectangle(-38,-85,76,125),Phaser.Geom.Rectangle.Contains);
    container.on('pointerup',(pointer:Phaser.Input.Pointer)=>{if (pointer.event.target instanceof HTMLCanvasElement && !document.querySelector('dialog[open]') && !this.drag?.moved && this.engine.getSnapshot().actors[id].visible) this.onActor(id);});
    this.actorViews.set(id,container);
  }
  /** True while anybody stands on the given floor region. */
  private zoneOccupied(zoneId:string,state:ReturnType<StoryEngine['getSnapshot']>) {
    for(const actor of Object.values(state.actors)) {
      if(!actor.visible)continue;
      if(zoneAt(this.mapData,actor.col,actor.row)?.id===zoneId)return true;
    }
    return false;
  }
  sync() {
    if(!this.cameras?.main)return;
    const state=this.engine.getSnapshot();
    this.roof?.setVisible(state.roofVisible);
    for(const {view,object} of this.artViews) {
      // A building's roof lifts as soon as somebody stands on the floor it covers,
      // so the interior paving and furnishings read through instead of a solid wall.
      const roofOff=object.interiorZone!==undefined && this.zoneOccupied(object.interiorZone,state);
      view.setVisible(object.visibility!=='exterior' || (state.roofVisible && !roofOff));
      // Until architectural front/back layers are authored, reveal walkers through the gate.
      const nearGate=Math.abs(state.actors.daiyu.col-13)<=1.5 && state.actors.daiyu.row>=22 && state.actors.daiyu.row<=26;
      view.setAlpha(view.texture.key==='flower-gate' && nearGate && this.mapData.id==='entry' ? .28 : 1);
    }
    const zoom=this.cameras.main.zoom;
    for(const label of this.placeLabels)label.setScale(1/zoom);
    // Keep the screen and walkers visible through the passage during its scene.
    this.passageRoof?.setVisible(!['N006','N007'].includes(this.engine.step.id));
    for (const [id,view] of this.actorViews) {
      const a=state.actors[id],p=project(a,this.mapData);
      const bounce=a.moving && !state.paused && !this.presentationPaused && !this.reducedMotion ? Math.sin(this.clock*.018)*2.5 : 0;
      const zoom=this.cameras.main.zoom;
      const asset=artAssets[id==='sedan'?'sedan-chair':`${id}-chibi`];
      const bodyHeight=asset?.height??85;
      const scale=Math.max(1,48/(bodyHeight*zoom));
      view.setScale(scale).setPosition(p.x,p.y+bounce).setVisible(a.visible).setDepth(p.y+1);
      // Iso walking right means col-row increases; mirror the sprite when the
      // painted chibi already faces the way it is looking, or away from it. The
      // direction survives a stop and a scene change, so a person who walked
      // left into a room — or was shown there facing someone — stays turned
      // that way until they move again, like a person turning on the spot.
      const sprite=this.actorSprites.get(id);
      if(sprite)sprite.setFlipX((a.direction===1)!==(paintedFacing(id,'chibi')==='right'));
      this.actorLabels.get(id)!.setScale(1/(zoom*scale)).setPosition(0,7/(zoom*scale));
    }
  }
  private declutterLabels(){
    const camera=this.cameras.main,zoom=camera.zoom,state=this.engine.getSnapshot();
    const occupied:{x:number;y:number;w:number;h:number}[]=[];
    const intersects=(a:{x:number;y:number;w:number;h:number},b:{x:number;y:number;w:number;h:number})=>a.x<b.x+b.w+4&&a.x+a.w+4>b.x&&a.y<b.y+b.h+3&&a.y+a.h+3>b.y;
    const priority=(id:ActorId)=>id===this.engine.step.speaker?0:id==='daiyu'?1:state.actors[id].moving?2:3;
    for(const [id,label] of [...this.actorLabels].sort((a,b)=>priority(a[0])-priority(b[0]))){
      const view=this.actorViews.get(id)!;if(!view.visible)continue;
      const x=(view.x-camera.worldView.x)*zoom,y=(view.y-camera.worldView.y)*zoom;
      const w=label.width,h=label.height;
      let offset=7,box={x:x-w/2,y:y+offset,w,h};
      // Stack labels locally when people stand close; sprites remain foot-anchored.
      for(let i=0;i<4&&occupied.some(b=>intersects(box,b));i++){offset+=h+3;box={...box,y:y+offset};}
      label.setY(offset/(zoom*view.scaleX)).setVisible(!occupied.some(b=>intersects(box,b)));
      if(label.visible)occupied.push(box);
    }
    for(const label of this.placeLabels){
      const box={x:(label.x-camera.worldView.x)*zoom-label.width/2,y:(label.y-camera.worldView.y)*zoom-label.height/2,w:label.width,h:label.height};
      label.setVisible(!occupied.some(b=>intersects(box,b)));if(label.visible)occupied.push(box);
    }
    const host=this.game.canvas.parentElement;
    if(host){
      const sizes=[...this.actorViews].filter(([,v])=>v.visible).map(([id,v])=>(artAssets[id==='sedan'?'sedan-chair':`${id}-chibi`]?.height??85)*v.scaleY*zoom);
      host.dataset.minActorPixels=String(sizes.length?Math.min(...sizes):0);
      host.dataset.labelPixels=String(Math.min(...[...this.actorLabels].filter(([id,l])=>state.actors[id].visible&&l.visible).map(([id,l])=>12*l.scaleY*this.actorViews.get(id)!.scaleY*zoom)));
    }
  }
  private drawActionFocus() {
    const trail=this.actionTrail,halo=this.actionHalo;if(!trail||!halo)return;
    trail.clear();halo.clear();
    const state=this.engine.getSnapshot();if(state.status!=='moving')return;
    if(state.effect) {
      const effect=state.effect,p=project(state.actors[effect.actor],this.mapData),t=effect.elapsed/effect.duration;
      halo.lineStyle(3,0xc39b51,.8);halo.strokeEllipse(p.x,p.y+4,60,26);
      if(effect.kind==='jade') {
        const x=p.x+Math.sin(t*Math.PI)*115,y=p.y-65+90*t-Math.sin(t*Math.PI)*70;
        halo.fillStyle(0xc7e2cf);halo.lineStyle(2,0x668675);halo.fillEllipse(x,y,14,21);halo.strokeEllipse(x,y,14,21);
        if(t>.65){halo.lineStyle(2,0xc7a36c,(1-t)*2);halo.strokeEllipse(p.x+65,p.y+20,50+(t-.65)*170,20+(t-.65)*70);}
      }else{halo.lineStyle(2,0xb99859,1-t);halo.strokeEllipse(p.x,p.y+3,55+t*50,24+t*20);}
    }
    for(const route of this.engine.movementPaths()) {
      const points=route.points.map(p=>project(p,this.mapData));if(points.length<2)continue;
      trail.lineStyle(route.actor==='daiyu'?6:3,route.actor==='daiyu'?0xb99451:0x809d89,.65);
      trail.beginPath();trail.moveTo(points[0].x,points[0].y);
      for(const p of points.slice(1))trail.lineTo(p.x,p.y);trail.strokePath();
      const end=points.at(-1)!;trail.lineStyle(2,0xb99451,.8);trail.strokeEllipse(end.x,end.y,34,16);
      for(let i=1;i<points.length;i++) {
        const a=points[i-1],b=points[i],t=this.reducedMotion ? .5 : (this.actionClock*.0008)%1;
        trail.fillStyle(0xfff4cb,.9);trail.fillCircle(a.x+(b.x-a.x)*t,a.y+(b.y-a.y)*t,3);
      }
      const p=points[0],pulse=this.reducedMotion?0:(Math.sin(this.actionClock*.005)+1)*.5;
      halo.lineStyle(2.5,0xc39b51,.65);halo.strokeEllipse(p.x,p.y+4,52+pulse*18,23+pulse*8);
      halo.lineStyle(1,0xfff5d5,.85);halo.strokeEllipse(p.x,p.y+4,40,18);
    }
  }
  private target() {
    const state=this.engine.getSnapshot(),map=this.engine.map;
    const moving=Object.values(state.actors).find(actor=>actor.visible&&actor.moving);
    const focus=state.actors.daiyu.visible?state.actors.daiyu:moving??map.anchors[state.focus];
    const p=project(focus,map);
    return {x:p.x,y:p.y-45+105/(this.cameras?.main?.zoom??1)};
  }
  private fit() {
    if(!this.cameras?.main)return;
    const size=Math.min(this.scale.width/1400,(this.scale.height-180)/650);
    this.cameras.main.setZoom(Phaser.Math.Clamp(size,.25,.9)*this.zoomFactor);
    const host=this.game.canvas.parentElement;
    if(host)host.dataset.zoom=String(this.cameras.main.zoom);
    this.sync();
  }
  recenter() {this.manual=false;this.zoomFactor=1;this.fit();}
  zoom(delta:number) {this.zoomFactor=Phaser.Math.Clamp(this.zoomFactor+delta,.65,2.5);this.fit();}
  guides(show:boolean) {this.routeGuide?.setVisible(show);this.grid?.setVisible(show);}
  update(time:number,delta:number) {
    this.clock=time;if(!this.engine.getSnapshot().paused&&!this.presentationPaused)this.actionClock+=delta;
    if(!this.presentationPaused)this.engine.tick(delta/1000);this.sync();this.drawActionFocus();this.declutterLabels();
    if(!this.manual) {
      const p=this.target(),camera=this.cameras.main;
      const targetX=p.x-camera.width/2,targetY=p.y-camera.height/2;
      if(this.engine.getSnapshot().paused) {
        // A paused stage must hold still: snap the camera instead of easing toward the
        // target, otherwise the view keeps drifting for a few frames after the pause.
        camera.scrollX=targetX;camera.scrollY=targetY;
      } else {
        const amount=this.reducedMotion?1:1-Math.exp(-delta/240);
        camera.scrollX=Phaser.Math.Linear(camera.scrollX,targetX,amount);camera.scrollY=Phaser.Math.Linear(camera.scrollY,targetY,amount);
      }
    }
  }
}
