/** 换场景 / 回目开篇时的「大地图定位转场」。
 *
 *  小场景图只画一间屋、一处院，读者看不出它落在荣国府的哪一角、更看不出
 *  这一回是在姑苏还是京城。这里用两拍把层级交代清楚：
 *
 *    第一拍（progress 0 → .44）天下舆图：光点从上一处所在区域飞到新区域，
 *      面包屑只亮「天下舆图」；
 *    第二拍（.44 → 1）分两种：
 *      - 府内层（京城 / 荣国府 / 宁国府 / 大观园）：天下图淡出、目标层淡入，
 *        光点从层入口飞到目标院落，面包屑逐级点亮，目标点高亮；
 *      - 天下层本身（姑苏、扬州、太虚、京郊…共 20 个 scene）：这些地方没有
 *        更细的一级可钻，硬切到一张无地名的空点阵图反而更空，改为留在天下图
 *        上「推镜」——目标区域平移到画面中心并放大，补到位光环与地名浮签。
 *
 *  刻意不做的几件事（都是踩过的坑）：
 *  - **不吞指针**：覆盖层 pointer-events:none，只有「跳过」按钮接事件。读者
 *    随时能点「继续剧情」，既有浏览器测试也不会被一层看不见的遮罩拦住。
 *  - **不改 inMotion、不暂停引擎**：转场是给地图区域换一层画面，不是一次
 *    演出；顶栏按钮、对白面板、自动播放、存档状态机都不该因它改变。
 *  - **不盖全屏**：只覆盖 map-panel，封面 / 封底（z-index 58）仍旧压在最上。
 *  - **不复用 WorldMap**：那是读者主动打开的可交互总览，只有 28 个考据建筑，
 *    而剧情有 45 个 scene，18 个在它上面查无此地。
 */
import { useMemo } from 'react';
import {
  placeOf, regionPoint, detailPoint, breadcrumbs, regionName,
  levelDots, regionDots, bezier, ease, isoOf, levelNames,
} from './scenePlaces.ts';

export type Locator = {
  scene: string;
  fromScene: string | null;
  book: number;
  bookName: string;
  reason: 'scene' | 'chapter';
  /** 0 → 1，由 App 的定时器推进。 */
  progress: number;
};

type Props = {
  locator: Locator;
  reducedMotion: boolean;
  onSkip: () => void;
};

// viewBox 只框住内容实际占用的那一段（等距投影后 y 约 110–560），
// 留太多内部空白会让 meet 缩放受高度限制、地图缩成画面中央一小块。
const W = 1000, H = 500, Y0 = 80;
const SWITCH = 0.44;
/** 两拍之间交叉淡入淡出的宽度。 */
const BLEND = 0.09;

const clamp01 = (v: number) => Math.max(0, Math.min(1, v));
const smooth = (v: number) => { const k = clamp01(v); return k * k * (3 - 2 * k); };

/** 等距网格底纹：让画面读起来是张地图，而不是一张散点图。 */
function IsoGrid({ level }: { level: string }) {
  const iso = useMemo(() => isoOf(level), [level]);
  const lines: { x1: number; y1: number; x2: number; y2: number }[] = [];
  for (let c = -4; c <= 44; c += 4) {
    const a = iso(c, 0), b = iso(c, 40);
    lines.push({ x1: a.x, y1: a.y, x2: b.x, y2: b.y });
    const d = iso(0, c), e = iso(40, c);
    lines.push({ x1: d.x, y1: d.y, x2: e.x, y2: e.y });
  }
  return <g className="locator-grid" aria-hidden="true">
    {lines.map((l, i) => <line key={i} x1={l.x1} y1={l.y1} x2={l.x2} y2={l.y2} stroke="#829670" strokeWidth=".8" opacity=".34" />)}
  </g>;
}

/** 一个地点标记。非目标点只画点、不写名字：一层里十几个点全标字会糊成一团
 *  （实测过），方位靠「点阵 + 顶部那张地名卡」交代更清楚。 */
function Dot({ x, y, active }: { x: number; y: number; active?: boolean }) {
  return <g className="locator-dot" opacity={active ? 1 : 0.75}>
    <ellipse cx={x} cy={y} rx={active ? 17 : 9} ry={active ? 8 : 4.5} fill="#5e7157" opacity=".2" />
    <circle cx={x} cy={y} r={active ? 7.5 : 4.2} fill={active ? '#b8792f' : '#77896d'} stroke="#fdf8e9" strokeWidth="1.8" />
  </g>;
}

export function SceneLocator({ locator, reducedMotion, onSkip }: Props) {
  const { scene, fromScene, bookName, reason, progress } = locator;
  const place = placeOf(scene);
  const level = place?.level ?? 'realm';
  const region = regionName(scene);
  // 天下层场景的面包屑原本只有「天下舆图」一级，第二拍就没有任何可点亮的
  // 进展。补上所在区域名，推镜时也能逐级亮起，和府内下钻的读法一致。
  const crumbs = useMemo(() => {
    const base = breadcrumbs(scene);
    return level === 'realm' && base.length === 1 ? [...base, regionName(scene)] : base;
  }, [scene, level]);

  // reduced-motion 下不做任何位移动画：直接把第二拍的终点静态画出来，
  // 读者一样能看清方位，只是没有飞过去的那一秒。
  const p = reducedMotion ? 1 : clamp01(progress);
  const first = clamp01(p / SWITCH);
  const second = clamp01((p - SWITCH) / (1 - SWITCH));
  const blend = smooth((p - (SWITCH - BLEND)) / (BLEND * 2));
  // 场景本身在「天下」层（姑苏、扬州、太虚、京郊…共 20 个）时没有更深的
  // 一级可钻，切到一张没标签的空点阵图反而更空。这类场景两拍都留在天下图，
  // 第二拍改成「镜头推近到目标区域」；只有府内层才做真正的下钻。
  const drill = level !== 'realm';
  const realmOpacity = drill ? 1 - blend : 1;
  const detailOpacity = drill ? blend : 0;
  const approach = drill ? 0 : ease(second);
  const zoom = 1 + approach * 0.2;
  const cx = W / 2, cy = Y0 + H / 2;

  const fromRegion = useMemo(() => fromScene ? regionPoint(fromScene) : regionPoint(scene), [fromScene, scene]);
  const toRegion = useMemo(() => regionPoint(scene), [scene]);
  // translate(T - z·P) scale(z) 恰好把点 P 映射到 T。approach=0 时 T=P、z=1，
  // 变换恒等，第一拍完全不受影响；approach→1 时目标区域被推到画面中心并放大。
  const focus = {
    x: toRegion.x + (cx - toRegion.x) * approach,
    y: toRegion.y + (cy - toRegion.y) * approach,
  };
  const realmTransform = `translate(${(focus.x - zoom * toRegion.x).toFixed(2)} ${(focus.y - zoom * toRegion.y).toFixed(2)}) scale(${zoom.toFixed(4)})`;
  const calloutAlpha = drill ? 0 : smooth((second - .3) / .5);
  const callout = useMemo(() => {
    const label = place?.name ?? region;
    return { label, w: Math.max(128, label.length * 13 + 30) };
  }, [place?.name, region]);
  const target = useMemo(() => detailPoint(scene), [scene]);
  // 第二拍的起点：从画面左下方「入城」，而不是凭空出现在目标点旁边。
  const entry = useMemo(() => ({ x: target.x - 150, y: target.y + 72 }), [target]);

  const realmToken = bezier(fromRegion, toRegion, ease(first), 58);
  const detailToken = bezier(entry, target, ease(second), 42);
  const dots = useMemo(() => levelDots(level), [level]);
  const regionDotsList = useMemo(() => regionDots(), []);
  // 下钻后的点阵必须带地名，否则读者看到的是一片没名字的点，等于没交代方位。
  // 全标会糊成一团（实测过），所以：取名字末段作短名 → 目标点排第一 → 按
  // 距目标由近及远贪心放置，与已放置标签会重叠的就省略，保证画面永远干净。
  const detailLabels = useMemo(() => {
    const shortName = (name: string) => {
      const parts = name.split('·').map(s => s.trim()).filter(Boolean);
      return (parts.length > 1 ? parts[parts.length - 1] : name).slice(0, 9);
    };
    const ranked = dots
      .map(d => ({ scene: d.scene, x: d.point.x, y: d.point.y, label: shortName(d.name) }))
      .sort((a, b) => (a.scene === scene ? -1 : b.scene === scene ? 1 :
        Math.hypot(a.x - target.x, a.y - target.y) - Math.hypot(b.x - target.x, b.y - target.y)));
    const placed: { x: number; y: number; w: number }[] = [];
    const out: { scene: string; x: number; y: number; label: string; w: number }[] = [];
    for (const d of ranked) {
      const w = d.label.length * 11 + 12;
      const box = { x: d.x - w / 2, y: d.y + 10, w };
      if (placed.some(q => Math.abs(q.x - box.x) < (q.w + w) / 2 + 6 && Math.abs(q.y - box.y) < 17)) continue;
      placed.push(box);
      out.push({ ...d, w });
    }
    return out;
  }, [dots, scene, target]);

  // 面包屑逐级点亮：第一拍只亮第一级，第二拍按进度把后面的点亮。
  const litCount = p < SWITCH ? 1 : 1 + Math.floor(second * (crumbs.length - 1) + 0.001) + (second > 0.02 ? 1 : 0);

  return <div className="scene-locator" role="status" aria-live="polite"
    aria-label={`方位：${crumbs.join(' › ')} · ${place?.name ?? scene}`} data-testid="scene-locator"
    data-scene={scene} data-reason={reason} data-progress={p.toFixed(3)} data-reduced={reducedMotion ? 'yes' : 'no'}
    data-level={level} data-drill={drill ? 'yes' : 'no'} data-from-scene={fromScene ?? ''}>
    {/* 一张卡把回目、层级、地名、跳过都收在顶部居中：左上角是「当前场景 /
        本回行迹」切换、右上角是缩放工具条、下方两侧是立绘，把信息放在底部会
        被立绘压住，放在左右会被工具条挡住（都在实测截图里出现过）。 */}
    <div className="locator-head">
      <span className="locator-kicker">{reason === 'chapter' ? `${bookName} · 开卷` : `${bookName} · 移步`}</span>
      <nav className="locator-crumbs" aria-label="舆图层级">
        {crumbs.map((c, i) => <span key={c} className={i < Math.min(litCount, crumbs.length) ? 'lit' : ''}>
          {i > 0 && <i aria-hidden="true">›</i>}{c}
        </span>)}
      </nav>
      <strong className="locator-place-name">{place?.name ?? scene}</strong>
      {/* 开卷不是「从某地移步到某地」——光点没动，写「移步」会自相矛盾。 */}
      <small className="locator-place-meta">{p < SWITCH && fromScene && fromScene !== scene ? `自 ${region} 一带移步` : `${levelNames[level] ?? level} · ${region}`}{place?.note ? ` · ${place.note}` : ''}</small>
      <button className="locator-skip" onClick={onSkip} aria-label="跳过方位示意">跳过 <span aria-hidden="true">→</span></button>
    </div>

    <svg className="locator-svg" viewBox={`0 ${Y0} ${W} ${H}`} preserveAspectRatio="xMidYMid meet" aria-hidden="true">
      <defs>
        <radialGradient id="locator-glow">
          <stop offset="0%" stopColor="#f0c879" stopOpacity=".85" />
          <stop offset="100%" stopColor="#f0c879" stopOpacity="0" />
        </radialGradient>
        <filter id="locator-soft"><feGaussianBlur stdDeviation="3" /></filter>
      </defs>

      {/* ---- 第一拍：天下舆图（天下层场景的第二拍也留在这张图上推镜） ---- */}
      <g data-layer="realm" data-zoom={zoom.toFixed(3)} opacity={realmOpacity} transform={realmTransform}>
        <IsoGrid level="realm" />
        {regionDotsList.map(r => <g key={r.key} className="locator-region" opacity={r.key === (place?.region ?? 'capital') ? 1 : 0.72}>
          <polygon points={`${r.point.x},${r.point.y - 38} ${r.point.x + 86},${r.point.y} ${r.point.x},${r.point.y + 38} ${r.point.x - 86},${r.point.y}`}
            fill={r.tone === 'myth' ? '#b9b5d0' : r.tone === 'water' ? '#a9c4cb' : r.tone === 'city' ? '#cbc097' : '#b9c9a2'}
            stroke={r.key === (place?.region ?? 'capital') ? '#9a7640' : '#879a78'} strokeWidth={r.key === (place?.region ?? 'capital') ? 2 : 1.1} opacity=".9" />
          <text x={r.point.x} y={r.point.y + 5} textAnchor="middle" fontSize="14" fontWeight="600" fill="#3f5340">{r.name}</text>
        </g>)}
        {fromScene && fromScene !== scene && <Dot x={fromRegion.x} y={fromRegion.y} />}
        <polyline points={`${fromRegion.x},${fromRegion.y} ${realmToken.x},${realmToken.y}`} fill="none" stroke="#a9702b" strokeWidth="3" strokeDasharray="7 5" opacity=".85" />
        <circle cx={realmToken.x} cy={realmToken.y} r="24" fill="url(#locator-glow)" />
        <circle cx={realmToken.x} cy={realmToken.y} r="8.5" fill="#c8872f" stroke="#fff6e2" strokeWidth="2.5" />
        <circle cx={toRegion.x} cy={toRegion.y} r={26 + 8 * (1 - first)} fill="none" stroke="#a9702b" strokeWidth="2.5" opacity={first > .6 ? .9 : .45} />
        {/* 天下层没有更深的一级可钻：靠「到位光环 + 地名浮签」交代『就是这里』，
            而不是切到一张没有地名的空点阵图（实测过，那样信息反而变少）。 */}
        {!drill && second > .62 && <g>
          <circle cx={toRegion.x} cy={toRegion.y} r={30 + 18 * (1 - second)} fill="none" stroke="#b8792f" strokeWidth="2" opacity={.7 * (1 - second) / .38} />
          <circle cx={toRegion.x} cy={toRegion.y} r="18" fill="url(#locator-glow)" />
        </g>}
        {!drill && calloutAlpha > 0 && <g opacity={calloutAlpha} transform={`translate(0 ${((1 - calloutAlpha) * 10).toFixed(2)})`}>
          <rect x={toRegion.x - callout.w / 2} y={toRegion.y + 48} width={callout.w} height="27" rx="13.5" fill="#fbf6e8" stroke="#c8b48a" strokeWidth="1.2" />
          <text x={toRegion.x} y={toRegion.y + 66} textAnchor="middle" fontSize="13" fontWeight="600" fill="#6b4d24">{callout.label}</text>
        </g>}
      </g>

      {/* ---- 第二拍：下钻到目标层 ---- */}
      <g data-layer="detail" opacity={detailOpacity} transform={`translate(${(1 - detailOpacity) * 26} ${(1 - detailOpacity) * -14}) scale(${1 - (1 - detailOpacity) * .06})`}
        style={{ transformOrigin: `${W / 2}px ${Y0 + H / 2}px` }}>
        <IsoGrid level={level} />
        {/* 该层的地点点阵：读者看到的是「一张府院图」，不是孤零零一个点 */}
        {dots.map(d => <Dot key={d.scene} x={d.point.x} y={d.point.y} active={d.scene === scene} />)}
        {detailLabels.map(d => <text key={d.scene} className="locator-dot-label"
          x={d.x} y={d.y + 24} textAnchor="middle" fontSize={d.scene === scene ? 13 : 11}
          fontWeight={d.scene === scene ? 700 : 500}
          fill={d.scene === scene ? '#6b4d24' : '#5d6d55'}>{d.label}</text>)}
        <polyline points={`${entry.x},${entry.y} ${detailToken.x},${detailToken.y}`} fill="none" stroke="#a9702b" strokeWidth="3" strokeDasharray="7 5" opacity=".85" />
        <circle cx={detailToken.x} cy={detailToken.y} r="25" fill="url(#locator-glow)" />
        <circle cx={detailToken.x} cy={detailToken.y} r="9" fill="#c8872f" stroke="#fff6e2" strokeWidth="2.5" />
        {/* 目标点从下钻一开始就有一圈定位环，读者不必等光点飞到才知道看哪儿。 */}
        <circle cx={target.x} cy={target.y} r="27" fill="none" stroke="#a9702b" strokeWidth="2" strokeDasharray="5 4" opacity=".65" />
        {/* 目标点到位后的高亮：脉冲圈 + 光晕 */}
        {second > .72 && <g>
          <circle cx={target.x} cy={target.y} r={20 + 12 * (1 - second)} fill="none" stroke="#b8792f" strokeWidth="2" opacity={.7 * (1 - second) / .28} />
          <circle cx={target.x} cy={target.y} r="13" fill="url(#locator-glow)" />
        </g>}
      </g>
    </svg>

  </div>;
}
