import facingTable from '../design/character-facing.json' with { type:'json' };
import buildTable from '../design/actor-builds.json' with { type:'json' };
import sections from '../design/chapter03-sections.json' with { type:'json' };
import script from '../design/chapter03-story.json' with { type:'json' };
import script1 from '../design/chapter01-story.json' with { type:'json' };
import script2 from '../design/chapter02-story.json' with { type:'json' };
import sections1 from '../design/chapter01-sections.json' with { type:'json' };
import sections2 from '../design/chapter02-sections.json' with { type:'json' };
import script4 from '../design/chapter04-story.json' with { type:'json' };
import sections4 from '../design/chapter04-sections.json' with { type:'json' };
import script5 from '../design/chapter05-story.json' with { type:'json' };
import sections5 from '../design/chapter05-sections.json' with { type:'json' };
import script6 from '../design/chapter06-story.json' with { type:'json' };
import sections6 from '../design/chapter06-sections.json' with { type:'json' };
import script7 from '../design/chapter07-story.json' with { type:'json' };
import sections7 from '../design/chapter07-sections.json' with { type:'json' };
import script8 from '../design/chapter08-story.json' with { type:'json' };
import sections8 from '../design/chapter08-sections.json' with { type:'json' };
import script9 from '../design/chapter09-story.json' with { type:'json' };
import sections9 from '../design/chapter09-sections.json' with { type:'json' };
import script10 from '../design/chapter10-story.json' with { type:'json' };
import sections10 from '../design/chapter10-sections.json' with { type:'json' };
import script11 from '../design/chapter11-story.json' with { type:'json' };
import sections11 from '../design/chapter11-sections.json' with { type:'json' };
import script12 from '../design/chapter12-story.json' with { type:'json' };
import sections12 from '../design/chapter12-sections.json' with { type:'json' };
import script13 from '../design/chapter13-story.json' with { type:'json' };
import sections13 from '../design/chapter13-sections.json' with { type:'json' };
import script14 from '../design/chapter14-story.json' with { type:'json' };
import sections14 from '../design/chapter14-sections.json' with { type:'json' };
import script15 from '../design/chapter15-story.json' with { type:'json' };
import sections15 from '../design/chapter15-sections.json' with { type:'json' };
import script16 from '../design/chapter16-story.json' with { type:'json' };
import sections16 from '../design/chapter16-sections.json' with { type:'json' };
import script17 from '../design/chapter17-story.json' with { type:'json' };
import sections17 from '../design/chapter17-sections.json' with { type:'json' };
import script18 from '../design/chapter18-story.json' with { type:'json' };
import sections18 from '../design/chapter18-sections.json' with { type:'json' };
import script19 from '../design/chapter19-story.json' with { type:'json' };
import sections19 from '../design/chapter19-sections.json' with { type:'json' };
import script20 from '../design/chapter20-story.json' with { type:'json' };
import sections20 from '../design/chapter20-sections.json' with { type:'json' };
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
  menzi:{name:'门子',fullName:'门子',color:0x8d8a72,css:'#8d8a72',relation:'应天府门子',description:'原是葫芦庙里的小沙弥。庙火之后无处安身，蓄了发充作衙门门子，认出任知府的雨村。'},
  plaintiff:{name:'原告',fullName:'冯家仆人',color:0x8a7f6d,css:'#8a7f6d',relation:'冯家老仆',description:'主人冯渊被薛家豪奴打死，凶身逃逸，他告了一年的状无人作主。'},
  xuepan:{name:'薛蟠',fullName:'薛蟠',color:0x6d8bab,css:'#6d8bab',relation:'薛家公子',description:'字文起，金陵皇商。五岁上性情奢侈，言语傲慢，终日斗鸡走马。人命官司被他视为儿戏，入京后日日受纨绔引诱，比当日更坏十倍。'},
  xueyima:{name:'薛姨妈',fullName:'薛姨妈',color:0x9c8ea6,css:'#9c8ea6',relation:'薛家寡母',description:'京营节度使王子腾之妹，与王夫人一母所生。为约束儿子执意住进荣府梨香院，声明日用供给一概免却。'},
  baochai:{name:'宝钗',fullName:'薛宝钗',color:0x8fb3a6,css:'#8fb3a6',relation:'薛家小姐',description:'乳名宝钗，比薛蟠小两岁。肌骨莹润，举止娴雅，读书识字胜过乃兄。随母兄进京待选，与黛玉、迎春等日日同处。'},
  jinghuan:{name:'警幻',fullName:'警幻仙姑',color:0x7b5ea8,css:'#7b5ea8',relation:'太虚幻境之主',description:'居离恨天之上、灌愁海之中，司人间风情月债。奉荣宁二公之灵嘱，引宝玉入梦，历演金陵十二钗判词与红楼梦十二支，以情欲声色警其痴顽。'},
  qin_ke:{name:'可卿',fullName:'秦可卿',color:0xb56f8a,css:'#b56f8a',relation:'贾蓉之妻 · 宝玉梦中兼美',description:'贾蓉之妻，金陵十二钗之末，乳名兼美字可卿。宝玉梦中，警幻以妹许之，教以云雨之事；人间结局见于第十三回。'},
  liu_lao:{name:'刘姥姥',fullName:'刘姥姥',color:0x9c7a4c,css:'#9c7a4c',relation:'狗儿之岳母 · 乡间老妪',description:'积年穷寡妇，膝下无儿，依女婿狗儿过活。因与金陵王家连过宗，携外孙板儿进荣国府攀亲，得凤姐周济二十两银子。'},
  ban_er:{name:'板儿',fullName:'板儿',color:0xc9a86a,css:'#c9a86a',relation:'狗儿之子 · 刘姥姥外孙',description:'狗儿与刘氏之子，才五六岁的孩子。随刘姥姥进荣府，因闹着要吃肉、不肯作揖，是刘姥姥进府的陪衬。'},
  zhou_rui:{name:'周瑞家的',fullName:'周瑞家的',color:0x8a7da0,css:'#8a7da0',relation:'王夫人陪房 · 凤姐之下',description:'王夫人的陪房媳妇，丈夫周瑞。昔年争买田地多得狗儿之父之力，故引刘姥姥去见凤姐，是荣府对外的接引人。'},
  ping_er:{name:'平儿',fullName:'平儿',color:0xb59a7a,css:'#b59a7a',relation:'凤姐心腹通房大丫头',description:'凤姐的心腹通房大丫头，处事妥帖。刘姥姥初进院时误认她为凤姐；奉凤姐命取二十两银子与一吊钱周济刘姥姥。'},
  jia_rong:{name:'贾蓉',fullName:'贾蓉',color:0x6f8fb0,css:'#6f8fb0',relation:'贾珍之子 · 秦可卿之夫',description:'宁国府贾珍之子，秦可卿之夫。十七八岁，轻裘宝带、美服华冠。来向凤姐借玻璃炕屏，于刘姥姥在场时闯入，令其坐立不安。'},
  ying_er:{name:'莺儿',fullName:'黄金莺',color:0xd8a0a0,css:'#d8a0a0',relation:'宝钗贴身大丫鬟',description:'薛宝钗的贴身大丫鬟，本名黄金莺，聪明伶俐、口齿爽利。第八回中替宝钗捧出金锁，失言点破金玉良缘之配。'},
  qin_zhong:{name:'秦钟',fullName:'秦钟',color:0x9aa8d8,css:'#9aa8d8',relation:'秦可卿之弟',description:'秦业之子，秦可卿之弟，眉清目秀、举止风流，与宝玉气味相投。第九回附学贾府家塾，与宝玉同窗。'},
  jia_rui:{name:'贾瑞',fullName:'贾瑞',color:0xa0a060,css:'#a0a060',relation:'贾代儒之孙',description:'贾代儒之孙，管着家塾，图便宜没刚性。受薛蟠银钱便假公济私，第九回闹学堂中一味弹压不力。'},
  jin_rong:{name:'金荣',fullName:'金荣',color:0xc09060,css:'#c09060',relation:'金氏之侄',description:'贾府正派玄孙，父母早亡，跟着寡母过活，性泼皮。与薛蟠旧有纠葛，第九回当面讥讽秦钟、宝玉。'},
  ming_yan:{name:'茗烟',fullName:'茗烟',color:0x88b0a0,css:'#88b0a0',relation:'宝玉小厮',description:'宝玉最得用的小厮，机灵忠勇。第九回闻主子受辱，闯进家塾与金荣扭打。'},
  li_gui:{name:'李贵',fullName:'李贵',color:0xb08868,css:'#b08868',relation:'宝玉奶兄',description:'宝玉的奶兄，老实粗壮，在宝玉房中管事。第九回闹学堂时赶来喝住众顽童。'},
  you_shi:{name:'尤氏',fullName:'尤氏',color:0xa88fa0,css:'#a88fa0',relation:'贾珍之妻 · 宁府当家奶奶',description:'宁国府贾珍的继室，当家奶奶。性子圆融能持事，待下宽和。第十回里对璜大奶奶细说秦可卿的病，第十一回主持贾敬寿辰的家宴。'},
  jia_zhen:{name:'贾珍',fullName:'贾珍',color:0x8a6f5a,css:'#8a6f5a',relation:'宁国府当家',description:'宁国府当家，贾敬之子、贾蓉之父，世袭三品爵威烈将军。一味高乐、不理家事，于秦可卿之病却着实焦心，第十回听冯紫英荐了张友士来诊。'},
  jin_shi:{name:'金氏',fullName:'璜大奶奶',color:0xc08570,css:'#c08570',relation:'贾璜之妻 · 金荣姑母',description:'贾璜之妻，人称璜大奶奶，金荣的姑母。守着些小产业，时常到宁荣二府请安、奉承凤姐与尤氏。第十回听得侄儿受欺，怒冲冲要往宁府理论。'},
  hu_shi:{name:'胡氏',fullName:'金寡妇',color:0x9a8f80,css:'#9a8f80',relation:'金荣之母',description:'金荣的母亲，守寡多年，靠人周济度日。第十回里劝儿子忍气吞声：这一处念书的地方来得不易，闹出去比登天还难。'},
  zhang_youshi:{name:'张友士',fullName:'张友士',color:0x7a8f88,css:'#7a8f88',relation:'冯紫英之师 · 儒医',description:'冯紫英幼时从学的先生，学问渊博、医理极精。第十回上京为儿子捐官，受荐为秦可卿诊脉，论病源断为忧虑伤脾、肝木忒旺，开益气养荣补脾和肝汤。'},
  jia_qiang:{name:'贾蔷',fullName:'贾蔷',color:0x8fa8c0,css:'#8fa8c0',relation:'贾府正派玄孙',description:'贾府正派玄孙，父母早亡，随贾珍过活，与贾蓉交好。第十一回在宁府帮着照应宾客，第十二回受凤姐指派捉弄贾瑞。'},
  dai_quan:{name:'戴权',fullName:'戴权',color:0x8a7f9a,css:'#8a7f9a',relation:'大明宫掌宫内相',description:'大明宫掌宫内相，掌内廷之职。第十三回首七第四日亲来宁府上祭，贾珍趁机求他为贾蓉捐龙禁尉，约定「平准一千二百两银子，送到我家就完了」。'},
  bao_zhu:{name:'宝珠',fullName:'宝珠',color:0xb59ab0,css:'#b59ab0',relation:'秦氏义女',description:'秦氏身前的小丫鬟。因见秦氏身无所出，甘心愿为义女，誓任摔丧驾灵之任；贾珍传下，从此皆呼宝珠为小姐，按未嫁女之丧在灵前哀哀欲绝。'},
  lai_sheng:{name:'来升',fullName:'来升',color:0x8d8a72,css:'#8d8a72',relation:'宁国府总管',description:'宁国府中都总管。第十四回因凤姐协理而传齐同事人等，说「那是个有名的烈货，脸酸心硬」，又传凤姐「卯正二刻我来点卯」的定规。'},
  zhao_er:{name:'昭儿',fullName:'昭儿',color:0x9aa8b8,css:'#9aa8b8',relation:'贾琏小厮',description:'贾琏打发回京报信的小厮。第十四回报林如海九月初三日巳时去世、贾琏送林姑娘同送灵到苏州；凤姐连夜打点大毛衣服交付他带回扬州。'},
  shui_rong:{name:'水溶',fullName:'北静王水溶',color:0x6f8fb0,css:'#6f8fb0',relation:'北静王 · 四王之一',description:'北静郡王，年未弱冠，形容秀美，情性谦和，不以王位自居。第十四回为秦氏之丧设路奠，第十五回路谒时问「那一位是衔宝而诞者」，并以圣上亲赐的鹡鸰香念珠赠宝玉。'},
  jing_xu:{name:'净虚',fullName:'净虚',color:0x9c8ea6,css:'#9c8ea6',relation:'水月庵老尼',description:'馒头庵（水月庵）住持。第十五回求凤姐出头替长安县张家退亲事，愿出三千银子；凤姐应下后，净虚奉承她越发受用。'},
  zhi_neng:{name:'智能儿',fullName:'智能儿',color:0xd8a0a0,css:'#d8a0a0',relation:'水月庵小尼 · 秦钟所恋',description:'净虚的徒弟。第十五回渐知风月，看上秦钟人物风流，二人情投意合；夜里秦钟来寻智能，被宝玉撞破。'},
  er_ya_tou:{name:'二丫头',fullName:'二丫头',color:0xc9a86a,css:'#c9a86a',relation:'村庄纺车丫头',description:'铁槛寺附近村庄的丫头，十七八岁，纺车纺线。第十五回与宝玉、秦钟在庄上相遇，纺车被宝玉拧转作耍。'},
  wang_er:{name:'旺儿',fullName:'旺儿',color:0xb08868,css:'#b08868',relation:'凤姐小厮',description:'凤姐的小厮。第十五回奉命修书长安，托主文相公假托贾琏所嘱向节度使云光说合张家退亲之事，两日妥协。'},
  qin_ye:{name:'秦业',fullName:'秦业',color:0x8a8278,css:'#8a8278',relation:'秦钟之父',description:'秦钟之父，年迈多病。第十三回携秦钟来宁府吊唁；第十五回因年迈多病不能随众住在铁槛寺，只命秦钟等待安灵。'},
  jia_dairu:{name:'贾代儒',fullName:'贾代儒',color:0x8a8278,css:'#8a8278',relation:'家塾塾师 · 贾瑞祖父',description:'贾家义学的塾师，贾瑞的祖父。素日教训最严，不许贾瑞多走一步。第十二回因子孙一夜不归动了家法，后又为孙儿的重病各处请医。'},
  yuanchun:{name:'元春',fullName:'贾元春',color:0x9a5a78,css:'#9a5a78',relation:'宝玉的姐姐 · 才选凤藻宫',description:'贾政与王夫人的长女，贤孝才德，选入宫中。第十六回晋封凤藻宫尚书，加封贤德妃，荣国府由此筹备省亲。'},
  jia_huan:{name:'贾环',fullName:'贾环',color:0x7d8a9c,css:'#7d8a9c',relation:'贾政庶子 · 赵姨娘所出',description:'贾政与赵姨娘所生，宝玉同父异母的弟弟。少年心性狭窄，因围棋赖钱被赵姨娘责骂，又被凤姐当众数落。'},
  zhao_yiniang:{name:'赵姨娘',fullName:'赵姨娘',color:0x9c8878,css:'#9c8878',relation:'贾政之妾 · 贾环生母',description:'贾政之妾，贾环生母。性情乖僻，忌刻正房，见儿子受委屈便迁怒辱骂。'},
  shi_xiangyun:{name:'湘云',fullName:'史湘云',color:0xc98a72,css:'#c98a72',relation:'宝玉的表姐 · 史湘云',description:'贾母侄孙女，父母早亡，寄养于叔婶。性情爽朗豪阔，爱说爱笑，口齿带一点咬舌。第二十回正式登场。'},
  she_yue:{name:'麝月',fullName:'麝月',color:0x8a9bb0,css:'#8a9bb0',relation:'宝玉房中丫鬟',description:'怡红院中较稳重的丫鬟。众姊妹顽耍时独守外间看屋，宝玉为她篦头。'},
  jia_lian:{name:'贾琏',fullName:'贾琏',color:0x6f8fb0,css:'#6f8fb0',relation:'凤姐之夫 · 黛玉的表兄',description:'贾赦之子，协助料理荣府外务。第十四回送黛玉往扬州奔丧，第十六回事毕带黛玉回京。'},
};
export type ActorId=keyof typeof cast;
export type FacingSide='left'|'right';
export type ArtKind='portrait'|'chibi';

/** How tall a character stands on the map, as a multiple of the standard adult
 *  figure.
 *
 *  Every chibi bitmap is drawn on the same ~116px canvas and the map renders
 *  them one to one, so without this a five-year-old and a matriarch come out
 *  exactly as tall as a grown woman. The novel is full of that kind of
 *  contrast — 板儿 is a child who cannot keep up with the adults around him,
 *  刘姥姥 is a stooped village grandmother — and it reads on the stage only if
 *  the heights differ. */
const buildScaleOf=(build:string|undefined):number=>{
  if(!build)return 1;
  const entry=(buildTable.builds as Record<string,{scale:number}>)[build];
  return entry?entry.scale:1;
};
export const actorBuildScale=(id:ActorId):number=>
  buildScaleOf((buildTable.actors as Record<string,string>)[id]);


/** Which side each painted head is drawn facing.
 *
 * A character is not one picture. It is a portrait, a chibi sprite, and a set
 * of portrait emotion variants, each a separate bitmap that was painted
 * separately. The emotion variants were repainted by an image model and do
 * not all face the same way — the same grandmother faces one way in her
 * neutral portrait and another in her sad variant — so the facing is recorded
 * per asset, in design/character-facing.json, not per character.
 *
 * The painted direction decides whether a sprite is mirrored: a speaker stands
 * on the left of the dialogue panel and has to look towards the text, and a
 * walker has to look the way it is walking, so a head painted facing the other
 * way is flipped. The sedan is the exception: it is a vehicle carried by four
 * bearers whose heads turn inward, so the group has no single painted side and
 * keeps the left default, flipped with the direction of travel.
 */
const facingTableData=facingTable as {actors:Record<string,{portrait?:FacingSide;chibi?:FacingSide}>;variants?:Record<string,{facing:FacingSide}>};
const facing=facingTableData.actors;
const variants=facingTableData.variants??{};
export const paintedFacing=(actor:ActorId,kind:ArtKind):FacingSide=>facing[actor]?.[kind]??'left';
/** The facing of one exact bitmap, including an emotion variant.
 *
 * The variant carries its own painted head, so it is looked up by its own
 * key. A variant the table does not know falls back to the base portrait,
 * which is what it was painted from. */
export const paintedFacingOf=(assetKey:string,actor:ActorId,kind:ArtKind):FacingSide=>{
  const variant=variants[assetKey];
  if(variant)return variant.facing;
  return paintedFacing(actor,kind);
};
/** True when the painted head already faces the given side, so no mirror is needed. */
export const facesSide=(actor:ActorId,kind:ArtKind,side:FacingSide)=>paintedFacing(actor,kind)===side;
export type Move={type:'move';actor:ActorId;via:string[]};
export type Action=Move|{type:'parallel';moves:Move[]}|{type:'show';actor:ActorId;at:string}|{type:'hide';actor:ActorId}|{type:'roof';visible:boolean}|{type:'effect';actor:ActorId;kind:'jade'|'greet'|'rest'|'idle'|'anger';duration:number};
export type StoryStep={id:string;chapter:string;scene:string;title:string;place:string;focus:string;speaker:ActorId|'narrator';text:string;mood?:string;offscreen?:boolean;actions:Action[];source:{chapter:number;paragraphLead:string;textKind:string;layer?:string}};
export const chapter3Story=script as StoryStep[];
export const story=[...script1,...script2,...script,...script4,...script5,...script6,...script7,...script8,...script9,...script10,...script11,...script12,...script13,...script14,...script15,...script16,...script17,...script18,...script19,...script20] as StoryStep[];
/** Index of the last chapter-three node inside `story`; saves taken before chapter four
 * end here, and a saved ending at or before it must reopen as an ordinary reading state. */
export const LAST_LEGACY_INDEX=([...script1,...script2,...script] as StoryStep[]).length-1;
export const chapters=[...sections1,...sections2,...sections.map(s=>({...s,book:3})),...sections4,...sections5.map(s=>({...s,book:5})),...sections6.map(s=>({...s,book:6})),...sections7.map(s=>({...s,book:7})),...sections8.map(s=>({...s,book:8})),...sections9.map(s=>({...s,book:9})),...sections10.map(s=>({...s,book:10})),...sections11.map(s=>({...s,book:11})),...sections12.map(s=>({...s,book:12})),...sections13.map(s=>({...s,book:13})),...sections14.map(s=>({...s,book:14})),...sections15.map(s=>({...s,book:15})),...sections16.map(s=>({...s,book:16})),...sections17.map(s=>({...s,book:17})),...sections18.map(s=>({...s,book:18})),...sections19.map(s=>({...s,book:19})),...sections20.map(s=>({...s,book:20}))];
export const bookNames:Record<number,string>={1:"第一回",2:"第二回",3:"第三回",4:"第四回",5:"第五回",6:"第六回",7:"第七回",8:"第八回",9:"第九回",10:"第十回",11:"第十一回",12:"第十二回",13:"第十三回",14:"第十四回",15:"第十五回",16:"第十六回",17:"第十七回",18:"第十八回",19:"第十九回",20:"第二十回"};

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
