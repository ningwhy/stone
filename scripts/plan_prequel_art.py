"""Append chapter 1–2 cast and stage architecture, retaining every older source."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1];p=root/'art/generation-plan.json';d=json.loads(p.read_text());known={j['id'] for j in d['jobs']}
people={
'shiyin':('五十岁江南乡宦甄士隐，清瘦温厚，疏朗短须，灰青软帽，淡米色儒衫，青灰外袍，恬淡儒雅','man'),
'fengshi':('四十岁江南乡宦之妻封氏，温柔端庄，乌发低髻，一支素银簪，淡藕色交领长袄，灰青长裙，慈爱略含忧色','woman'),
'yinglian':('三岁江南小女孩甄英莲，圆润幼儿面容，眉心一粒小胭脂痣，两个小发髻，杏黄短袄和粉红小裙，天真乖巧，幼小儿童比例，绝不是成年女子','girl'),
'jiaoxing':('十七岁甄家丫鬟娇杏，清秀鹅蛋脸，乌发双髻，简朴杏色短袄与浅绿长裙，手持一枝小花，温婉，朴素侍女装束','woman'),
'fengsu':('六十岁乡村富农封肃，矮胖，灰黑短须，深棕瓜皮帽，赭褐布袍，暗灰马褂，精明世故，手拢在袖中','man'),
'monk':('红楼梦癞头和尚，五十岁清瘦僧人，头顶稀疏毛发与明显癞疮斑，灰褐破旧僧袍，赤足，笑容旷达，手持一枚小小碧绿玉石，神秘慈悲','man'),
'taoist':('红楼梦跛足道人，五十岁清瘦道人，蓬乱发髻，长须，灰蓝破旧道袍，草鞋，竹杖支撑右腿，飘逸旷达','man'),
'kongkong':('空空道人，六十岁道家游方文士，整齐灰白长须，深青道袍，布冠，手持纸卷，凝神阅读的姿态，宁静沉思','man'),
'huoqi':('甄家仆人霍启，三十五岁普通男仆，无须，深灰布帽，靛蓝短袄，灰褐长裤，束腰布带，朴实平常','man'),
'oldmonk':('智通寺龙钟老僧，八十岁瘦弱和尚，光头，白眉，深灰旧僧袍，微驼背，手持木勺，温和衰老','man')}
new=[]
for i,(id,(desc,subject)) in enumerate(people.items()):
 for k,kind in enumerate(['portrait','chibi']):
  prompt='红楼梦原创人物设定。'+desc+'。中国工笔淡彩水彩手绘，与古典游戏立绘统一。纯白背景，无建筑无文字无边框，单个人物。'
  prompt+= '头顶至腰下完整的半身立绘，正面略侧，头肩完整清楚，四周留白。' if kind=='portrait' else '三头身Q版全身游戏角色，大头小身体，完整脚底，轻微俯视等距，朝右下站立，无地面无投影，四周留白。'
  new.append(dict(id=f'{id}-{kind}',seed=10230100+i*2+k,size='768x1024',prompt=prompt,subject=subject))
places={
'estate-zhen':'姑苏甄士隐的江南小宅院，三间书房，白墙灰瓦木格窗，窗外花圃芭蕉，左右短回廊，清雅安静，完整院落轮廓',
'estate-hulu':'姑苏葫芦庙，狭窄古朴的江南小庙，单檐青灰瓦，土黄旧墙，木门微开，旁有窄小僧房，竹篱，没有大佛像',
'estate-farm':'江南乡村封肃田庄，几间灰瓦朴素农舍，竹篱小院，一角谷仓与两棵树，土黄色院墙，质朴乡村宅院',
'estate-yamen':'古代知府衙署前院，三开间公堂，暗红木门柱与青灰屋顶，白色院墙和石阶，规整完整小院，无室内家具外露',
'estate-zhitong':'偏僻山村智通寺，破败的小寺院，歪斜门楼，剥落米黄墙，灰绿苔痕屋顶，稀疏竹林，旁有小小煮粥炉，完整建筑，无人物',
'estate-tavern':'江南城郊小酒肆，一座两层灰瓦白墙木楼，一楼敞开前廊有木桌与茶壶，竹帘与素色酒旗，旁有柳树，雅致水彩游戏建筑',
'estate-lantern':'姑苏元宵花灯街，一组相连的三间江南灰瓦白墙商铺，屋檐悬挂多盏红灯笼与兔子花灯，木门楼，温暖古典街景，完整独立小建筑群',
'black-oil-gate':'古代府邸南墙上的黑油大门，黑色双扇木门，黄铜门环，青灰瓦小门楼，两侧连接米白院墙，门洞敞开可穿行，从南向北进入，绝不要红门',
'west-wall-gate':'古代府邸西侧院墙上的小角门，深褐木门与灰青瓦顶，两段白墙沿南北方向相接，门洞朝西敞开，完整独立门墙建筑，门洞可穿行'}
for i,(id,desc) in enumerate(places.items()):
 new.append(dict(id=id,seed=10230200+i,size='1024x1024',subject='building',prompt=desc+'。严格2比1菱形等距正交俯视，见南面与东面，水墨淡彩手绘灰青米白藕红配色，单个紧凑完整建筑素材，纯白背景，不要大地板不要漂浮岛，无人物无文字无标注，四周留白。'))
new.extend([
 dict(id='spirit-stone',seed=10230300,size='1024x1024',subject='rock',prompt='单块古典神话通灵顽石，青灰色嶙峋石块，淡淡玉绿光泽，石面几道天然纹理，不要任何文字，等距俯视2比1水彩手绘游戏素材，纯白背景，无底座无人，无大范围地面，主体完整'),
 dict(id='crimson-pearl',seed=10230301,size='1024x1024',subject='plant',prompt='单株红楼梦神话绛珠仙草，几片纤细深绿叶，顶端一颗红色珠状花苞，根部一块小小青石，露珠晶莹，古典工笔淡彩游戏素材，完整植物，等距俯视，纯白背景，无人物无文字')])
new.extend([{'id': 'manor-main-gate', 'seed': 10230400, 'size': '1024x1024', 'subject': 'building', 'prompt': '荣国府正门建筑，完整的一座三开间兽头大门，正中宽大朱红双扇木门，两旁各一扇窄门，门上铜兽面门环，五级白石阶，门前一对小石狮子，门楼连续灰绿硬山瓦屋顶，米白院墙，庄严宽敞的公侯府邸外门，不是垂花门，不是小花园门，不要院落大房子。单个独立建筑素材，严格二比一菱形正交等距俯视，见南面与东面，清雅工笔淡彩水彩手绘，纯白背景，无文字无签名，无人物，主体完整，四周留白。'}, {'id': 'estate-ruins', 'seed': 10230401, 'size': '1024x1024', 'subject': 'building', 'prompt': '江南小宅院遭大火后的废墟，原有三间房烧塌，只剩低矮的半截米白墙、炭黑木梁、青灰碎瓦堆，地面灰烬与砖石，小片荒草，无火焰无人无尸体，是完整清楚的小型废墟场景，不要正常房屋屋顶，不要神话石头。单个独立建筑素材，严格二比一菱形正交等距俯视，见南面与东面，清雅工笔淡彩水彩手绘，纯白背景，无文字无签名，无人物，主体完整，四周留白。'}])
new.append({'id': 'estate-ruins-v2', 'seed': 10230402, 'size': '1024x1024', 'subject': 'ruins', 'prompt': 'A compact heap of burnt rubble, remnants after a devastating fire. ALL ROOFS ARE GONE. Only three short broken plaster wall fragments remain, jagged broken wall tops, black charred timber beams lying horizontally on the ground, piles of broken gray clay roof tiles and fallen bricks, ash stains, sparse weeds. Maximum wall height is half a person. NO standing house, NO intact roofs, NO flames, NO people. Isometric 2:1 orthographic game prop viewed from southeast, exquisite Chinese ink and watercolor with muted gray sage and tan, entire object isolated on pure white, no text. 烧毁后的瓦砾场，房顶全部坍塌，只有低矮残墙、焦黑横木和碎砖瓦。'})
for j in new:
 if j['id'] not in known:d['jobs'].append(j)
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');(root/'art/prequel-art-ids.json').write_text(json.dumps([j['id'] for j in new if j['id']!='estate-ruins-v2']))
print(' '.join(j['id'] for j in new))
