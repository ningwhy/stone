"""Append missing cast pairs and architectural estate assets without replacing sources."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1];p=root/'art/generation-plan.json';plan=json.loads(p.read_text());known={j['id'] for j in plan['jobs']}
people={
'zhang':('四十岁清代汉族文士张如圭，清瘦长脸，短黑髭，深赭色长衫、青灰马褂，黑色软帽，手持折起的邸报，待人热切稳重','man'),
'leng':('四十五岁清代古董商人冷子兴，圆脸，细八字胡，黑色瓜皮帽，暗橄榄绿长衫与褐色马褂，一手握闭合折扇，精明健谈，微笑','man'),
'zheng':('五十岁清代贵族文官贾政，端方长脸，整齐黑须，黑色便帽，藏青长袍，灰青外褂，双手端庄交叠，严正儒雅','man'),
'guide':('六十岁清代荣国府引路嬷嬷，慈祥朴素的老妇，灰白头发盘成低髻，青褐布抹额，藕灰交领短袄和深棕裙，手向前略伸做引路手势，无金冠无贵族华服','woman'),
'maid':('十六岁清代荣国府侍女，双丫髻，细小红绳发饰，红绫夹袄与青绿长裙，双手自然相拢，精神伶俐，普通丫鬟装束而非贵族小姐','girl'),
'messenger':('四十岁清代宅门传话妇人，简朴低髻，素蓝头巾，灰蓝布袄深靛裙，双手交握，恭谨温和，不佩珠翠金饰','woman'),
'nurse_wang':('六十岁清代黛玉乳母王嬷嬷，慈祥的瘦小老妇，灰白低髻，深棕布抹额，浅灰蓝长袄、靛青裙，略弯腰，双手相拢，朴素无首饰','woman'),
'nurse_li':('五十五岁清代宝玉乳母李嬷嬷，丰圆面庞，黑灰头发整齐低髻，暗紫布抹额，褐紫短袄与墨绿裙，稳重严肃，手拢身前，朴素无贵族装饰','woman')}
new=[]
for i,(id,(description,subject)) in enumerate(people.items()):
 for k,kind in enumerate(['portrait','chibi']):
  key=f'{id}-{kind}'
  prompt='独立单个人物设定，红楼梦原创形象。'+description+'。清雅工笔淡彩手绘，人物衣服细节清楚，纯净纯白背景，背景无建筑、花纹、边框、文字或落款。'
  prompt+=('半身立绘，头顶至腰下完整，人物正面略向左，头肩清楚，双手完整，四周留白。' if kind=='portrait' else '三头身Q版游戏角色，大头小身，头部占身体三分之一，全身完整，脚底清楚，轻微俯视等距，朝右下站立，无地面无投影，四周留白。')
  new.append({'id':key,'seed':10222300+i*2+k,'size':'768x1024','prompt':prompt,'subject':subject})
architecture={
'estate-grandmother':'荣国府贾母正院，一座轩敞的北面五间上房，左右各一列低矮厢房与回廊，前方小垂花门，形成完整紧凑的四合院，正中敞亮石砖庭院，两株海棠，灰绿瓦顶、暗红梁柱、米白墙面，建筑庄重宽敞',
'estate-east':'清代荣国府东路贾赦院，一座小巧雅致的花园院落，黑油小门，三个前后相连的小门厅，后方三间正房，左右短廊，白墙青灰瓦，院中稀疏竹林和太湖石，小院轮廓清楚',
'estate-wang':'清代荣国府王夫人院，北侧正房与东廊三间小正房相接，西侧两间耳房，东廊红柱连续回廊，三面围合的紧凑小院，青灰瓦顶白墙，石阶院门，古雅安静，无室内家具外露',
'estate-feng':'清代荣国府王熙凤与贾琏居住的小院，入口一面粉油大影壁，影壁后敞开侧门，北面精致三间正屋，左右两翼抄手游廊围合，灰绿瓦顶，朱红门窗和细金线，院中一株石榴与两盆花，华贵利落',
'estate-rear':'清代贾母院北侧后房院，一座带东西耳房的五间长条正屋，前方短小院落和连廊，两侧白墙，青灰瓦顶朱红木窗，后房门敞开，整体是一栋完整建筑与院落，无桌子无碗碟无室内陈设外露',
'estate-bisha':'清代贵族府邸的内宅卧房建筑，贾母院后部的碧纱橱外观，一座精巧灰青瓦顶的三间长屋，青绿纱窗与花格木门，低矮耳房与窄檐回廊，安静小庭院，无床铺无屏风无家具外露，完整房屋屋顶',
'estate-study':'清代荣国府贾政书房院落，肃静三间书房主屋，深灰瓦顶、白墙、深褐木格窗，前有小阶与拱门，左右短厢房围出方形小院，院中一棵松树和山石，规整庄重，无桌子无茶具无室内家具外露'}
for i,(id,description) in enumerate(architecture.items()):
 new.append({'id':id,'seed':10222400+i,'size':'1024x1024','subject':'building','prompt':'可直接抠图用于等距地图的单个完整宅院建筑群素材。'+description+'。严格二比一菱形正交等距俯视，从东南侧看见南立面与东立面，屋顶可见，无透视消失点。院落与低矮围墙连成一个完整主体，紧凑方形占地，不要大范围地面底板，不要漂浮岛屿，不要人物。纯白背景，主体完整居中，四周留白，无文字无标注无签名。'})
for j in new:
 if j['id'] not in known:plan['jobs'].append(j)
p.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n');(root/'art/missing-art-ids.json').write_text(json.dumps([j['id'] for j in new],indent=2)+'\n')
print(' '.join(j['id'] for j in new))
