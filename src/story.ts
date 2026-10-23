import script from '../design/chapter03-story.json' with { type:'json' };
import sections from '../design/chapter03-sections.json' with { type:'json' };
import script1 from '../design/chapter01-story.json' with { type:'json' };
import script2 from '../design/chapter02-story.json' with { type:'json' };
import sections1 from '../design/chapter01-sections.json' with { type:'json' };
import sections2 from '../design/chapter02-sections.json' with { type:'json' };
export const cast = {
  oldmonk:{"name": "智通寺老僧", "fullName": "智通寺老僧", "color": 8885375, "css": "#87947f", "relation": "寺中煮粥人", "description": "龙钟衰老，回答雨村时答非所问；与癞头和尚分列。"},
  huoqi:{"name": "霍启", "fullName": "霍启", "color": 8885375, "css": "#87947f", "relation": "甄家家人", "description": "带英莲看灯，暂离后失去孩子，惧罪逃走。"},
  kongkong:{"name": "空空道人", "fullName": "空空道人", "color": 8885375, "css": "#87947f", "relation": "石头记抄录者", "description": "发现石上故事，与顽石论书，抄录问世；与跛足道人分列。"},
  taoist:{"name": "跛足道人", "fullName": "跛足道人", "color": 8885375, "css": "#87947f", "relation": "一僧一道", "description": "唱好了歌点醒甄士隐，带他离家而去。"},
  monk:{"name": "癞头和尚", "fullName": "癞头和尚", "color": 8885375, "css": "#87947f", "relation": "一僧一道", "description": "神话中携顽石入世；在人间劝士隐舍英莲，与梦中仙师形象相通。"},
  fengsu:{"name": "封肃", "fullName": "封肃", "color": 8885375, "css": "#87947f", "relation": "士隐岳丈", "description": "大如州乡民，收留女婿，却在置办房地时半哄半赚。"},
  jiaoxing:{"name": "娇杏", "fullName": "娇杏", "color": 8885375, "css": "#87947f", "relation": "甄家丫鬟", "description": "采花时回顾雨村，后来被纳为二房，生子后扶正。"},
  yinglian:{"name": "甄英莲", "fullName": "甄英莲", "color": 8885375, "css": "#87947f", "relation": "士隐之女", "description": "三岁幼女，眉心有痣。元宵灯市失踪，此处保持幼童形象。"},
  fengshi:{"name": "封氏", "fullName": "封氏", "color": 8885375, "css": "#87947f", "relation": "士隐之妻", "description": "英莲失踪后思女成病，火后随夫投亲；丈夫出家后以针线度日。"},
  shiyin:{"name": "甄士隐", "fullName": "甄士隐", "color": 8885375, "css": "#87947f", "relation": "甄家主人", "description": "姑苏乡宦，资助贾雨村。失女、火灾与穷困之后，解好了歌，随道人而去。"},
  daiyu:{name:'黛玉',fullName:'林黛玉',color:0x799d9a,css:'#799d9a',relation:'故事视角',description:'林如海与贾敏之女。辞父入京，在外祖母家安身，凡事留心。'},
  grandmother:{name:'贾母',fullName:'贾母',color:0x96729a,css:'#96729a',relation:'黛玉的外祖母',description:'史太君，贾赦、贾政和贾敏的母亲，疼爱远来的外孙女。'},
  baoyu:{name:'宝玉',fullName:'贾宝玉',color:0xb65f5a,css:'#b65f5a',relation:'黛玉的表兄',description:'贾政与王夫人之子，衔玉而生。与黛玉初见，便认作旧相识。'},
  feng:{name:'凤姐',fullName:'王熙凤',color:0xa65a4c,css:'#a65a4c',relation:'黛玉的表嫂',description:'贾琏之妻，王夫人内侄女，料理荣府家务，言谈爽利。'},
  wang:{name:'王夫人',fullName:'王夫人',color:0x728565,css:'#728565',relation:'黛玉的二舅母',description:'贾政之妻，宝玉之母。带黛玉认座、告诫宝玉的性情。'},
  xing:{name:'邢夫人',fullName:'邢夫人',color:0x9d7c65,css:'#9d7c65',relation:'黛玉的大舅母',description:'贾赦之妻，亲自带黛玉往东路小院拜访大舅父。'},
  liwan:{name:'李纨',fullName:'李纨',color:0xa6a1a0,css:'#a6a1a0',relation:'黛玉的表嫂',description:'贾珠之妻，在贾母处陪侍、晚膳时捧饭。'},
  yingchun:{name:'迎春',fullName:'贾迎春',color:0xb7a365,css:'#b7a365',relation:'黛玉的表姊妹',description:'三春之一，温柔沉默、观之可亲。'},
  tanchun:{name:'探春',fullName:'贾探春',color:0xa58ba9,css:'#a58ba9',relation:'黛玉的表姊妹',description:'三春之一，俊眼修眉、顾盼神飞，初见时笑问宝玉赠字的来历。'},
  xichun:{name:'惜春',fullName:'贾惜春',color:0xc198a3,css:'#c198a3',relation:'黛玉的表姊妹',description:'三春中年纪幼小的一位，与姊姊们同来相见。'},
  xiren:{name:'袭人',fullName:'花袭人',color:0xc09b86,css:'#c09b86',relation:'宝玉的贴身丫鬟',description:'原名珍珠，原侍贾母，后给宝玉；夜间宽慰因摔玉自责的黛玉。'},
  xueyan:{name:'雪雁',fullName:'雪雁',color:0x7c9cb3,css:'#7c9cb3',relation:'黛玉自幼的丫鬟',description:'十岁，随黛玉从扬州入京。'},
  yingge:{name:'鹦哥',fullName:'鹦哥',color:0x9c95b0,css:'#9c95b0',relation:'贾母拨给黛玉的丫鬟',description:'第三回以鹦哥之名出场，随侍碧纱橱，向袭人说起黛玉伤心之事。'},
  yucun:{name:'雨村',fullName:'贾雨村',color:0x5c7d8c,css:'#5c7d8c',relation:'黛玉的塾师',description:'托林如海向贾政求荐，复职后补授应天府。'},
  ruhai:{name:'如海',fullName:'林如海',color:0x879da5,css:'#879da5',relation:'黛玉的父亲',description:'丧妻后劝女依傍外祖母，修荐书帮助雨村。'},
  zheng:{name:'贾政',fullName:'贾政',color:0x677d6d,css:'#677d6d',relation:'黛玉的二舅父',description:'帮助雨村复职。黛玉来拜时因斋戒未见。'},
  zhang:{name:'张如圭',fullName:'张如圭',color:0x888476,css:'#888476',relation:'雨村旧日同僚',description:'向雨村告知朝廷准许旧员起复的消息。'},
  leng:{name:'冷子兴',fullName:'冷子兴',color:0x978775,css:'#978775',relation:'雨村的友人',description:'为雨村出主意，请林如海转荐贾政。'},
  guide:{name:'引路嬷嬷',fullName:'引路嬷嬷',color:0x9a9274,css:'#9a9274',relation:'府中引路人',description:'代表入府接应、引路的婆子群体。'},
  maid:{name:'丫鬟',fullName:'通报丫鬟',color:0xc39789,css:'#c39789',relation:'府中侍女',description:'代表门前通报、奉茶、侍膳的丫鬟群体。'},
  messenger:{name:'来人',fullName:'传话来人',color:0x8a927d,css:'#8a927d',relation:'传话人',description:'在不同场景代表贾赦的传话人、王家派来的媳妇，不作为同一原著人物。'},
  nurse_wang:{name:'王嬷嬷',fullName:'王嬷嬷',color:0x99907e,css:'#99907e',relation:'黛玉的乳母',description:'年老，随黛玉从扬州入京，夜间在碧纱橱陪侍。'},
  nurse_li:{name:'李嬷嬷',fullName:'李嬷嬷',color:0x9a8a82,css:'#9a8a82',relation:'宝玉的乳母',description:'在外间与袭人照管宝玉。'},
  sedan:{name:'轿子',fullName:'入府小轿',color:0xa36557,css:'#a36557',relation:'入府交通',description:'代表入府乘轿；拜访贾赦所乘翠幄青紬车另以转场叙述。'},
};
export type ActorId=keyof typeof cast;
/** Chibi/portrait art is painted facing one side; walking or seating on the other side needs a mirror. Default is left. */
export const facingRight=new Set<ActorId>(['fengsu','monk','kongkong','oldmonk','leng','xichun','xing','xiren','yucun','zheng']);
export type Move={type:'move';actor:ActorId;via:string[]};
export type Action=Move|{type:'parallel';moves:Move[]}|{type:'show';actor:ActorId;at:string}|{type:'hide';actor:ActorId}|{type:'roof';visible:boolean}|{type:'effect';actor:ActorId;kind:'jade'|'greet'|'rest';duration:number};
export type StoryStep={id:string;chapter:string;scene:string;title:string;place:string;focus:string;speaker:ActorId|'narrator';text:string;mood?:string;offscreen?:boolean;actions:Action[];source:{chapter:number;paragraphLead:string;textKind:string;layer?:string}};
export const chapter3Story=script as StoryStep[];
export const story=[...script1,...script2,...script] as StoryStep[];
export const chapters=[...sections1,...sections2,...sections.map(s=>({...s,book:3}))];
export const bookNames:Record<number,string>={1:"第一回",2:"第二回",3:"第三回"};

/** Consecutive move actions for different actors describe one shared walk; play them together
 * so a two-person errand no longer costs twice the stage time. Same-actor neighbours stay
 * sequential (the engine forbids moving one actor twice in parallel). */
function parallelize(steps: StoryStep[]): StoryStep[] {
  const group=(moves: Move[]): Action[] => {
    const batches: Move[][]=[];
    for(const move of moves) {
      const last=batches.at(-1);
      if(last&&!last.some(m=>m.actor===move.actor))last.push(move); else batches.push([move]);
    }
    return batches.map(b=>b.length===1?b[0]:{type:'parallel',moves:b});
  };
  return steps.map(step=>{
    if(!step.actions.some(a=>a.type==='move'))return step;
    const actions: Action[]=[]; let buffer: Move[]=[];
    const flush=()=>{if(buffer.length){actions.push(...group(buffer));buffer=[];}};
    for(const action of step.actions) {
      if(action.type==='move')buffer.push(action); else {flush();actions.push(action);}
    }
    flush();
    return {...step,actions};
  });
}
export const stagedStory=parallelize(story);
