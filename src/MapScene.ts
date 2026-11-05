import Phaser from 'phaser';
import { artAssets, artGround, artImage } from './art.ts';
import { project, zoneAt } from './model.ts';
import type { ArtObject, MapData } from './model.ts';
import { cast, paintedFacingOf } from './story.ts';
import { audio } from './audio.ts';
import { STEP_FILE } from './audio.ts';
import type { StepSurface } from './audio.ts';
import type { ActorId } from './story.ts';
import type { StoryEngine } from './engine.ts';

/** Everything on the stage sorts by its isometric ground line — buildings by their
 * calibrated anchor, walkers by their feet — so a wall standing nearer the camera
 * covers a person behind it. The player must still always see the person they are
 * moving, so anything occluding a walker goes translucent instead of hiding them.
 * Halo sits above the walkers, place labels above that. */
const HALO_DEPTH = 5001;
const PLACE_LABEL_DEPTH = 5002;

/** What the walkers on this stage are standing on. Only the canal has no ground: `lin`
 *  shares the river theme with it because there is water in the Lin courtyard, and its
 *  residents quite reasonably walk on stone. The lane outside the wall is dust, whatever
 *  its garden theme says. */
export function stepSurface(map: MapData): StepSurface {
  if (map.id === 'canal') return 'oar';
  if (map.id === 'guowai') return 'earth';
  if (map.theme === 'interior' || map.theme === 'formal') return 'board';
  return 'stone';
}

export class MapScene extends Phaser.Scene {
  engine: StoryEngine;
  mapData: MapData;
  actorViews = new Map<ActorId, Phaser.GameObjects.Container>();
  private actorSprites = new Map<ActorId, Phaser.GameObjects.Image>();
  roof?: Phaser.GameObjects.Graphics;
  artViews: {view:Phaser.GameObjects.Image;object:ArtObject}[] = [];
  grid?: Phaser.GameObjects.Graphics;
  private roomSkirting?: Phaser.GameObjects.Graphics;
  passageRoof?: Phaser.GameObjects.Graphics;
  routeGuide?: Phaser.GameObjects.Graphics;
  actionTrail?: Phaser.GameObjects.Graphics;
  actionHalo?: Phaser.GameObjects.Graphics;
  private actionClock = 0;
  manual = false;
  presentationPaused = false;
  private placeLabels:Phaser.GameObjects.Text[]=[];
  private actorLabels=new Map<ActorId,Phaser.GameObjects.Text>();
  /** Horizontal alpha span per row band, sampled once per texture. See silhouetteOf(). */
  private silhouettes=new Map<string,Uint8Array[]>();
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
    // Warm the effects this stage will use so the first footfall is not late. The theme
    // piece itself is requested by App; here we only queue, because the context does not
    // exist until the reader's first gesture.
    // Warm the effects this stage will use so the first footfall is not late. The stage
    // only ever asks for the one footfall its own surface has, but the UI chime and the
    // page are wanted everywhere.
    for(const effect of [STEP_FILE[stepSurface(this.mapData)],'sfx-tap','sfx-page','sfx-door','sfx-bell','sfx-chair'])audio.warm(effect);
  }
  /** A raised stone platform. The dream stages have no estate paving, so without one the
   *  furniture sits on the bare wash and reads as cut-out stickers dropped on a page. The
   *  two faces turned toward the camera are drawn as a plinth, which is what makes the
   *  props read as standing *on* something. */
  private terrace(g:Phaser.GameObjects.Graphics,c:number,r:number,w:number,h:number,kind:'court'|'path') {
    // A `court` is jade-white platform stone on a dream stage; a `path` is the warm grey
    // slab of an estate 甬路, laid over the courtyard tiles and cut into single stones.
    const stone=kind==='path'
      ? {top:0xe6dcc3,side:0xbfb49a,seam:0xa89c80,drop:7,step:1}
      : {top:0xeaf0e3,side:0xc4d1c0,seam:0xb9c7b5,drop:12,step:2};
    const drop=stone.drop;
    const north=this.p(c,r),east=this.p(c+w,r),south=this.p(c+w,r+h),west=this.p(c,r+h);
    // Cast shadow on the page, then the plinth, then the slab on top.
    g.fillStyle(0x8ba294,.09);
    g.beginPath();g.moveTo(north.x,north.y+drop+5);g.lineTo(east.x,east.y+drop+5);g.lineTo(south.x,south.y+drop+9);g.lineTo(west.x,west.y+drop+9);g.closePath();g.fillPath();
    g.fillStyle(stone.side,.9);
    g.beginPath();g.moveTo(east.x,east.y);g.lineTo(south.x,south.y);g.lineTo(south.x,south.y+drop);g.lineTo(east.x,east.y+drop);g.closePath();g.fillPath();
    g.beginPath();g.moveTo(south.x,south.y);g.lineTo(west.x,west.y);g.lineTo(west.x,west.y+drop);g.lineTo(south.x,south.y+drop);g.closePath();g.fillPath();
    g.lineStyle(1,0x9fb1a0,.5);
    g.lineBetween(east.x,east.y+drop,south.x,south.y+drop);g.lineBetween(south.x,south.y+drop,west.x,west.y+drop);
    g.fillStyle(stone.top,1);
    g.beginPath();g.moveTo(north.x,north.y);g.lineTo(east.x,east.y);g.lineTo(south.x,south.y);g.lineTo(west.x,west.y);g.closePath();g.fillPath();
    // Paving seams along both axes, plus a kerb line, so the slab is stone not paper.
    g.lineStyle(1,stone.seam,.32);
    for(let cc=c+stone.step;cc<c+w;cc+=stone.step){const a=this.p(cc,r),b=this.p(cc,r+h);g.lineBetween(a.x,a.y,b.x,b.y);}
    for(let rr=r+stone.step;rr<r+h;rr+=stone.step){const a=this.p(c,rr),b=this.p(c+w,rr);g.lineBetween(a.x,a.y,b.x,b.y);}
    g.lineStyle(1,0xa9b9a6,.5);
    g.beginPath();g.moveTo(north.x,north.y);g.lineTo(east.x,east.y);g.lineTo(south.x,south.y);g.lineTo(west.x,west.y);g.closePath();g.strokePath();
  }
  /** Courtyard enclosure: a plastered wall with a grey tile coping, drawn under the props
   *  so a hall still stands over its own wall. Gaps between segments are the gates, which
   *  is how a Chinese courtyard states its plan — without them the buildings read as a
   *  scattering of roofs on open ground. */
  private courtyardWalls() {
    if(!this.mapData.walls.length) return;
    const g=this.add.graphics().setDepth(-9900);
    const H=36;
    for(const [c1,r1,c2,r2] of this.mapData.walls) {
      const a=this.p(c1,r1),b=this.p(c2,r2);
      // A wall is a face with height, not a line on the ground: a plastered panel standing
      // 36 px proud of its base, a tiled coping on top, and a cast shadow at the foot. A
      // flat band in the paving colour simply vanished into the tiles.
      g.fillStyle(0x6f7562,.12);
      g.beginPath();g.moveTo(a.x,a.y+4);g.lineTo(b.x,b.y+4);
      g.lineTo(b.x,b.y+16);g.lineTo(a.x,a.y+16);g.closePath();g.fillPath();
      g.fillStyle(0xded2b6,1);
      g.beginPath();g.moveTo(a.x,a.y);g.lineTo(b.x,b.y);
      g.lineTo(b.x,b.y-H);g.lineTo(a.x,a.y-H);g.closePath();g.fillPath();
      // A hairline course of bricks halfway up, so a long wall still has scale.
      g.lineStyle(1,0xc2b696,.55);g.lineBetween(a.x,a.y-H*.45,b.x,b.y-H*.45);
      g.fillStyle(0x76806f,1);
      g.beginPath();g.moveTo(a.x,a.y-H);g.lineTo(b.x,b.y-H);
      g.lineTo(b.x,b.y-H-7);g.lineTo(a.x,a.y-H-7);g.closePath();g.fillPath();
      g.lineStyle(1,0x59604f,.5);g.lineBetween(a.x,a.y-6,b.x,b.y-6);
    }
  }
  /** Hanging lanterns for a night street: a warm halo on the ground, then the lamp.
   *
   *  The 灯市 booths are painted bamboo frames, so without lights hanging from them the
   *  market played as a row of empty tents in broad daylight. A lantern is a cord, two
   *  rounded rects, a gold cap and a warm core — drawing it here keeps a dozen of them
   *  consistent and saves another 1024 px render that the image model would fill with a
   *  courtyard wall anyway. */
  private lanterns() {
    const halos=this.add.graphics().setDepth(-9960);
    // A lantern has to hang from something: rope the neighbours together along the street,
    // so the string reads as a string and not as lamps floating in the dark.
    const lit=this.mapData.lights.map(([c,r])=>this.p(c,r));
    for(let i=1;i<lit.length;i++){
      const a=lit[i-1],b=lit[i];
      if(Math.hypot(b.x-a.x,b.y-a.y)>420) continue;
      const rope=this.add.graphics().setDepth(Math.min(a.y,b.y)-90);
      rope.lineStyle(1.4,0x4a3b2c,.75);
      rope.beginPath();rope.moveTo(a.x,a.y-78);
      rope.lineTo((a.x+b.x)/2,Math.min(a.y,b.y)-78+9);
      rope.lineTo(b.x,b.y-78);rope.strokePath();
    }
    for(const [c,r] of this.mapData.lights) {
      const p=this.p(c,r);
      // Ground first: three soft discs, so the paving under a lantern reads as lit.
      for(const [rad,alpha] of [[52,.05],[32,.07],[17,.10]] as [number,number][]) {
        halos.fillStyle(0xffc46b,alpha); halos.fillCircle(p.x,p.y,rad);
      }
      const g=this.add.graphics().setDepth(p.y);
      g.lineStyle(1.6,0x5b4632,.9); g.lineBetween(p.x,p.y-78,p.x,p.y-46);
      g.fillStyle(0x8f2f28,1); g.fillRoundedRect(p.x-12,p.y-46,24,28,8);
      g.fillStyle(0xef5138,1); g.fillRoundedRect(p.x-9,p.y-43,18,22,7);
      g.fillStyle(0xffdda8,.9); g.fillEllipse(p.x,p.y-32,11,15);
      g.fillStyle(0x8a6d3f,1); g.fillRect(p.x-13,p.y-50,26,4); g.fillRect(p.x-10,p.y-20,20,3);
      g.fillStyle(0xb8352c,1); g.fillRect(p.x-1.5,p.y-17,3,9);
      g.fillStyle(0xd8543f,1); g.fillEllipse(p.x,p.y-7,7,5);
    }
  }
  private artwork() {    for(const object of this.mapData.art) {
      const ground=artGround(object);
      const image=this.add.image(object.x,object.y,object.asset).setOrigin(.5,1)
        .setDisplaySize(object.width,object.height).setDepth(ground.y+object.depthOffset);
      this.artViews.push({view:image,object});
      // Every prop gets a faint contact shadow at its own foot line. Sorted just under its
      // sprite, so a nearer prop still covers it. Skipped for whole buildings (they already
      // have their own painted ground shadow) and for the floating 仙珠.
      if(object.width<=700&&!object.asset.endsWith('pearl')) {
        const width=Math.min(object.width*.66,150);
        const shadow=this.add.graphics().setDepth(object.y-1);
        shadow.fillStyle(0x5f6b52,.07);shadow.fillEllipse(ground.x+2,ground.y+3,width*1.05,width*.34);
        shadow.fillStyle(0x5f6b52,.09);shadow.fillEllipse(ground.x,ground.y,width*.58,width*.17);
      }
    }
  }
  create() {
    const floor=this.add.graphics().setDepth(-10000);
    // The backdrop is a flat theme wash drawn well past the 40×40 playfield: stages
    // that hug the north or east edge (e.g. 太虚幻境's 警幻院/香闺 at row 3) put the
    // camera over the map border, and a 0..40 rect left a pale page-coloured wedge in
    // the corner. Painting a margin of the same colour keeps every stage full-bleed.
    this.rect(floor,-16,-16,72,72,this.mapData.theme==='night'?0xc7c9c5:this.mapData.theme==='myth'?0xd4d9c7:this.mapData.theme==='dream'?0xd9e5df:this.mapData.theme==='ruins'?0xd3cbbd:0xeee8d7);
    // Any stage may declare water: a river for the canal, a garden pond, or the ink-black
    // torrent of 迷津. The colour is the *place*, not the theme: 灵河 is a fairy stream and
    // stays jade even though the beat is a dream, while the same dream theme in 迷津 is
    // pitch. Painting every dream-stage river black turned 灵河 into a black wall.
    if(this.mapData.water.length){
      const ink=this.mapData.id==='c5_mijing'?0x2f3a36:this.mapData.theme==='ruins'?0x39433f
        :this.mapData.theme==='myth'?0x4c5a54:this.mapData.theme==='night'?0x53635f:0xa8c5c2;
      const dark=ink!==0xa8c5c2;
      const glint=dark?0x8d9a90:0xe1eee7;
      for(const [c,r,w,h] of this.mapData.water){
        // A bank first: a damp rim keeps a dark band from reading as a wall standing up.
        this.rect(floor,c-.2,r-.2,w+.4,h+.4,dark?0x6d7266:0x93a89f);
        this.rect(floor,c,r,w,h,ink);
        // A slow bank of foam where the current runs, so a black stream still reads as water.
        floor.lineStyle(dark?2:1,glint,dark?.30:.40);
        for(let cc=c+1;cc<c+w-1;cc++)for(let rr=r+1;rr<r+h-1;rr+=3){const p=this.p(cc,rr);floor.lineBetween(p.x,p.y,p.x+35,p.y+3);}
      }
    }

    // Seeded paper grain, garden islands and inset paving avoid a uniform debug grid.
    let seed=102166;
    const random=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
    for(let i=0;i<3600;i++) {
      const p=this.p(random()*40,random()*40);
      floor.fillStyle(random()>.5?0x9d9576:0xffffff,.07);floor.fillCircle(p.x,p.y,random()*2.5+.5);
    }
    // Same grain for the margin ring, so the extended wash doesn't read as a
    // smoother band around the map proper.
    for(let i=0;i<2600;i++) {
      const c=random()*72-16,r=random()*72-16;
      if(c>=0&&c<=40&&r>=0&&r<=40)continue;
      const p=this.p(c,r);
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
    // Planting is per-courtyard now: a stage lists its own beds, and an empty list means
    // paving, dust or water instead of the old seven estate beds in every garden alike.
    for(const [c,r,w,h] of this.mapData.beds) {
      this.rect(floor,c,r,w,h,0x9fae86);this.rect(floor,c+.15,r+.15,w-.3,h-.3,0xb9c19c);
      // A bed is a planting, not a green rectangle: a hedge along the kerb, then clumps of
      // blossom on the diagonal grid the rest of the garden uses. At the zoom the game
      // actually plays at, a single 4 px speckle per cell vanished and the bed read as lawn.
      floor.lineStyle(3,0x7f8f68,.85);
      for(const [x1,y1,x2,y2] of [[c,r,c+w,r],[c+w,r,c+w,r+h],[c+w,r+h,c,r+h],[c,r+h,c,r]]) {
        const a=this.p(x1,y1),b=this.p(x2,y2);floor.lineBetween(a.x,a.y,b.x,b.y);
      }
      for(let i=0;i<Math.max(6,w*h*1.6);i++) {
        const p=this.p(c+.4+random()*(w-.8),r+.4+random()*(h-.8));
        const hue=random();
        floor.fillStyle(0x6f7f5a,.5);floor.fillEllipse(p.x,p.y+2,9+random()*7,3);
        floor.fillStyle(hue>.62?0xf0cdd2:hue>.3?0xf6efe0:0xe6b6bd,.92);
        floor.fillCircle(p.x,p.y-1,2.6+random()*2.2);
        floor.fillStyle(0xfdf8ee,.75);floor.fillCircle(p.x-1,p.y-2,1.1+random());
      }
    }
    // Platforms last, so they lie on top of the estate paving: a dream stage declares
    // them because it has no zone paving at all, while a courtyard uses one to lay a
    // stone 甬路 across its tiles.
    for(const t of this.mapData.terraces) this.terrace(floor,t.col,t.row,t.width,t.height,t.kind);
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
    // A 灯市 is played at night. Darkening the ground only — never the sprites — keeps the
    // lamps and the people lit while the paving falls away, which is what a night street does.
    if(this.mapData.dusk){
      const veil=this.add.graphics().setDepth(-9970);
      const pts=[this.p(-16,-16),this.p(56,-16),this.p(56,56),this.p(-16,56)];
      veil.fillStyle(0x2f3a52,.52);veil.beginPath();veil.moveTo(pts[0].x,pts[0].y);
      for(const q of pts.slice(1))veil.lineTo(q.x,q.y);
      veil.closePath();veil.fillPath();
    }
    this.courtyardWalls();
    this.lanterns();
    // Skirting for cut-away rooms: drawn above the floor and below every prop, redrawn on
    // each snapshot so it follows the room somebody walked into.
    this.roomSkirting=this.add.graphics().setDepth(-9880);
    this.artwork();
    if(this.mapData.id==='entry') {
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
      const label=this.add.text(p.x,p.y+80,text,{fontFamily:'"Songti SC", SimSun, serif',fontSize:'15px',color:'#332d1d',backgroundColor:'#fdf7e4',padding:{x:13,y:6}}).setOrigin(.5).setAlpha(.97).setShadow(0,1,'rgba(70,60,34,.45)',2,true,true).setDepth(PLACE_LABEL_DEPTH);this.placeLabels.push(label);
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
    this.actionHalo=this.add.graphics().setDepth(HALO_DEPTH);
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
    // One bell as the stage settles. It is silent until the reader has touched the page,
    // which is also when every other sound starts.
    audio.play('sfx-bell');
    const center=this.target();this.cameras.main.centerOn(center.x,center.y);
    this.onReady?.(this);
  }
  /** Where a prop's artwork actually is, cell by cell.
   *
   *  A sprite's rectangle is generous where the art is not: a cherry tree is a round crown
   *  inside a square box, a table is a slab and four legs with daylight between them, a
   *  bamboo clump is three stems and a lot of air. The difference decides whether a walker
   *  is *behind* the thing or merely standing in the empty part of its box, and that is the
   *  whole complaint about props fading on contact. So each texture is sampled once, at
   *  32×32, into an opacity grid — cheap (one drawImage, a four-kilobyte read) and cached
   *  for the whole scene. */
  private silhouetteOf(asset:string) {
    const cached=this.silhouettes.get(asset);
    if(cached)return cached;
    const empty:Uint8Array[]=[];
    this.silhouettes.set(asset,empty);
    if(!this.textures.exists(asset))return empty;
    const source=this.textures.get(asset).getSourceImage() as CanvasImageSource & {width?:number};
    if(!source||!(source.width??0))return empty;
    const n=32,canvas=document.createElement('canvas');
    canvas.width=n;canvas.height=n;
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    if(!ctx)return empty;
    ctx.drawImage(source,0,0,n,n);
    const data=ctx.getImageData(0,0,n,n).data,grid:Uint8Array[]=[];
    for(let y=0;y<n;y++) {
      const row=new Uint8Array(n);
      for(let x=0;x<n;x++) row[x]=data[(y*n+x)*4+3]>40?1:0;
      grid.push(row);
    }
    this.silhouettes.set(asset,grid);
    return grid;
  }
  /** The walls of a room whose roof has just come off.
   *
   *  Lifting the shell hides the whole building sprite — including the walls that gave
   *  the room its shape — and leaves furniture standing on open paving. A cut-away view
   *  needs the room's own skirting: a plastered base with a shadowed inner face along the
   *  three edges that still exist, and a gap where the door was, so the reader can tell a
   *  room from a courtyard. Drawn above the floor, below every prop. */
  private roomWalls(c:number,r:number,w:number,h:number) {
    const g=this.roomSkirting; if(!g)return;
    const n=this.p(c,r),e=this.p(c+w,r),s=this.p(c+w,r+h),wst=this.p(c,r+h);
    const height=30;
    const face=(a:{x:number;y:number},b:{x:number;y:number})=>{
      g.fillStyle(0x8c9280,.10);
      g.beginPath();g.moveTo(a.x,a.y);g.lineTo(b.x,b.y);g.lineTo(b.x,b.y+height+6);g.lineTo(a.x,a.y+height+6);g.closePath();g.fillPath();
      g.fillStyle(0xd6c8a6,1);
      g.beginPath();g.moveTo(a.x,a.y);g.lineTo(b.x,b.y);g.lineTo(b.x,b.y+height);g.lineTo(a.x,a.y+height);g.closePath();g.fillPath();
      g.lineStyle(2,0xa2937a,.9);g.lineBetween(a.x,a.y+height,b.x,b.y+height);
      g.lineStyle(4,0x6b7462,.75);g.lineBetween(a.x,a.y,b.x,b.y);
      g.lineStyle(1,0x8e7f66,.5);g.lineBetween(a.x,a.y+height*.5,b.x,b.y+height*.5);
    };
    // North and west edges stand behind the furniture; the south edge is left open — that
    // is the side the door was on, and it is also where the camera looks in.
    face(n,e); face(n,wst);
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
    const label=this.add.text(0,16,actor.name,{fontFamily:'"PingFang SC", sans-serif',fontSize:'13px',color:'#1f2e25',backgroundColor:'#fdf8e6',padding:{x:10,y:5}}).setOrigin(.5,0).setShadow(0,1,'rgba(52,64,50,.5)',2,true,true);container.add(label);this.actorLabels.set(id,label);
    container.setSize(75,110).setInteractive(new Phaser.Geom.Rectangle(-38,-85,76,125),Phaser.Geom.Rectangle.Contains);
    container.on('pointerup',(pointer:Phaser.Input.Pointer)=>{if (pointer.event.target instanceof HTMLCanvasElement && !document.querySelector('dialog[open]') && !this.drag?.moved && this.engine.getSnapshot().actors[id].visible){audio.play('sfx-tap');this.onActor(id);}});
    this.actorViews.set(id,container);
  }
  /** True while anybody stands on the given floor region. */
  private zoneOccupied(zoneId:string,state:ReturnType<StoryEngine['getSnapshot']>) {
    // Tested against the named rect, not through `zoneAt`: a room's floor always lies
    // inside the yard's floor, and `zoneAt` returns the *first* rect that contains the
    // cell — the yard — so the room would never count as occupied and its roof would
    // never lift. 贾政书房、甄宅书斋、智通寺大殿 were all standing open-roofed for this.
    const zone=this.mapData.zones.find(z=>z.id===zoneId);
    if(!zone)return false;
    for(const actor of Object.values(state.actors)) {
      if(!actor.visible)continue;
      if(actor.col>=zone.col && actor.col<zone.col+zone.width
         && actor.row>=zone.row && actor.row<zone.row+zone.height)return true;
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
      // Three states: `exterior` is the shell (visible while its roof is up, gone the
      // moment the room opens); `interior` is the furnishings, which must not stand in
      // the courtyard beside the house while the roof is still on; `always` is scenery.
      // An interior piece that names its room follows that room alone — a stage with two
      // halls would otherwise open both rooms at once.
      const shown=object.visibility==='exterior' ? (state.roofVisible && !roofOff)
        : object.visibility==='interior' ? (object.interiorZone!==undefined ? roofOff : !state.roofVisible || roofOff)
        : true;
      view.setVisible(shown);
    }
    this.roomSkirting?.clear();
    for(const z of this.mapData.zones) {
      if(!(z.indoor ?? false))continue;
      this.roomWalls(z.col,z.row,z.width,z.height);
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
      // Walkers sort against buildings and furniture by their isometric ground point,
      // like the artwork does, so a person north of a table stands behind it instead
      // of riding on top of it.
      view.setScale(scale).setPosition(p.x,p.y+bounce).setVisible(a.visible).setDepth(p.y);
      // Footfalls and creaking poles ride on the movement itself; audio.step throttles
      // repeats, and the sedan gets the wood rub instead of a footstep.
      if(a.moving && !state.paused && !this.presentationPaused) {
        if(id==='sedan')audio.play('sfx-chair',0.9);
        else audio.step(stepSurface(this.mapData));
      }
      // Iso walking right means col-row increases; mirror the sprite when the
      // painted chibi already faces the way it is looking, or away from it. The
      // direction survives a stop and a scene change, so a person who walked
      // left into a room — or was shown there facing someone — stays turned
      // that way until they move again, like a person turning on the spot.
      const sprite=this.actorSprites.get(id);
      const chibiKey=id==='sedan'?'sedan-chair':`${id}-chibi`;
      if(sprite)sprite.setFlipX((a.direction===1)!==(paintedFacingOf(chibiKey,id,'chibi')==='right'));
      this.actorLabels.get(id)!.setScale(1/(zoom*scale)).setPosition(0,7/(zoom*scale));
    }
    // Whether a prop goes translucent depends on *where the walker is standing*, not on
    // whether the two bitmaps overlap. A sprite rectangle cannot answer that question:
    // standing on the bed, in a doorway, under a tree, behind a screen and in front of it
    // all put the feet inside the same box, and fading the prop for every one of them is
    // what made the map feel like everything melts on contact.
    //
    // Three relations are told apart, in the order that matters:
    //
    //   on / inside — the feet are within the prop's footprint. The footprint is the
    //     ellipse its contact shadow is already drawn from, so the two agree by
    //     construction; a walker on the bed, in the gate's opening or at the foot of a
    //     tree stands *in* the thing, not behind it, and both must stay solid.
    //   in front    — feet south of the prop's foot line. Depth sorting already draws the
    //     walker on top, so there is nothing to fade.
    //   behind      — feet north of the foot line and within its width. Only this case
    //     hides somebody, and only here does the prop go translucent.
    //
    // …and "behind" still has to mean something: a walker whose feet are a hand's width
    // north of a low table loses a sliver of an ankle, and fading a 137 px table for that
    // reads as a glitch, not as a courtesy. The prop only fades once it actually covers a
    // quarter of the walker — below that, the person is legible anyway.
    //
    // The foot line is artGround(): props with a tall painted base (the flower gate puts
    // its feet 145 px above the bottom of its PNG) would otherwise fade while the walker
    // is still plainly in front of them.
    for(const {view,object} of this.artViews) {
      // A building shell never fades. Walking into it already lifts the whole shell off
      // the floor (see the `exterior` branch above), so the only case left is somebody
      // passing behind a house on the way somewhere else — and there the answer is the
      // name label, not a translucent roof: fading a 700 px house to 45 % turned the whole
      // courtyard into grey haze and still did not reveal a 85 px walker underneath it.
      if(!view.visible||object.flat||object.visibility==='exterior'){view.setAlpha(1);continue;}
      const ground=artGround(object);
      const top=object.y-object.height,left=object.x-object.width/2;
      const rows=this.silhouetteOf(object.asset);
      // Same ellipse as the contact shadow: a wide prop is capped at 150 px of contact,
      // because a 900 px hall only touches the ground along its plinth.
      const foot=Math.min(object.width*.66,150);
      const rx=foot*1.05/2,ry=foot*.34/2;
      let behind=false;
      for(const [id,actor] of Object.entries(state.actors)) {
        if(!actor.visible)continue;
        const p=project(actor,this.mapData);
        if(p.y>=ground.y)continue;                          // in front of it
        if(p.y<=top)continue;                               // beyond its tallest reach
        const dx=(p.x-ground.x)/rx,dy=(p.y-ground.y)/ry;
        if(dx*dx+dy*dy<=1)continue;                         // standing on / inside it
        // Walk the body from feet to crown and ask, band by band, whether the artwork is
        // actually there at this x. Six samples is enough to tell a tree crown from the
        // empty corner of the tree's box, and a table top from the gap under it.
        const body=artAssets[`${id}-chibi`]?.height??85;
        const u=(p.x-left)/object.width;
        let hits=0,seen=0;
        const samples=6;
        for(let i=0;i<samples;i++) {
          const y=p.y-body*(i+.5)/samples;
          const t=(y-top)/object.height;
          if(t<0||t>=1)continue;
          seen++;
          if(!rows.length) {                                 // texture never sampled
            if(Math.abs(p.x-object.x)<=object.width*.3)hits++;
            continue;
          }
          const grid=rows[Math.floor(t*rows.length)];
          // A walker is ~40 px wide; at 32 samples a body spans about a cell either side.
          const ix=Math.round(u*(grid.length-1));
          if(grid[ix]||grid[ix-1]||grid[ix+1])hits++;
        }
        // Only the bands the body actually reaches count: a walker taller than the prop
        // has their head out in the open, and that part must not vote.
        if(!seen||hits/seen<.55)continue;
        behind=true;break;
      }
      view.setAlpha(behind?.45:1);
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
      host.dataset.labelPixels=String(Math.min(...[...this.actorLabels].filter(([id,l])=>state.actors[id].visible&&l.visible).map(([id,l])=>{const size=typeof l.style.fontSize==='number'?l.style.fontSize:parseFloat(String(l.style.fontSize))||13;return size*l.scaleY*this.actorViews.get(id)!.scaleY*zoom;})));
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
      }else if(effect.kind==='anger') {
        const r=30+t*40;
        halo.lineStyle(3,0xc0392b,.85);halo.strokeEllipse(p.x,p.y+4,58,26);
        halo.lineStyle(3,0xe74c3c,1-t);halo.strokeEllipse(p.x,p.y+3,r,r*0.45);
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
    // Only the stage the story is currently on may drive the engine. When the story
    // moves to another map, the old scene lives a few frames longer until React swaps
    // the Phaser game — without this guard it would keep simulating the new stage's
    // walk, so characters were already moving before the new map ever loaded.
    if(!this.presentationPaused&&this.engine.getSnapshot().sceneId===this.mapData.id)this.engine.tick(delta/1000);this.sync();this.drawActionFocus();this.declutterLabels();
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
