import { useEffect, useState } from 'react';
import { artImage } from './art.ts';

const TIPS = [
  '正在铺开描金地图…',
  '正在唤出大观人物…',
  '正在点亮荣国府的灯…',
  '正在展开前三回画册…',
];
const SCENE_TIPS = [
  '正在铺纸上石…',
  '正在描入院墙…',
  '正在整理衣妆…',
  '正在点亮檐下灯…',
];
const RUNNERS = ['daiyu-chibi', 'baoyu-chibi', 'feng-chibi'];
const ROTATE_KEY = 'honglou-rotate-dismissed';

/** Shared painted road: walkers trot along the fill and a status line rotates. */
function Road({progress, tips, interval = 2600}: {progress: number; tips: string[]; interval?: number}) {
  const [tip, setTip] = useState(0);
  useEffect(() => {
    const timer = setInterval(() => setTip((t) => (t + 1) % tips.length), interval);
    return () => clearInterval(timer);
  }, [tips, interval]);
  const pct = Math.max(0, Math.min(100, Math.round(progress * 100)));
  return <>
    <div className="loading-track">
      <div className="loading-fill" style={{ width: `${pct}%` }} />
      {RUNNERS.map((key, i) => (
        <img
          key={key}
          className={`loading-runner runner-${i}`}
          src={artImage(key)}
          alt=""
          style={{ left: `calc(${pct}% - ${14 + i * 26}px)` }}
        />
      ))}
    </div>
    <p className="loading-status" aria-live="polite">{pct}% · {tips[tip]}</p>
  </>;
}

/** First-paint stage: Q-version walkers trot along a painted road while Phaser preloads the scene. */
export function LoadingScreen({ progress, done }: { progress: number; done: boolean }) {
  return (
    <div className="loading-screen" role="status" aria-label="正在加载地图与人物" data-done={done}>
      <div className="loading-inner">
        <div className="loading-brand">
          <span className="brand-seal">红</span>
          <span className="loading-title">红楼一隅</span>
        </div>
        <p className="loading-sub">黛玉初入贾府 · 等距叙事地图</p>
        <Road progress={progress} tips={TIPS}/>
      </div>
    </div>
  );
}

/** Scene change stage: the map keeps its previous frame underneath, so waiting looks deliberate. */
export function SceneLoadingCard({ title, progress }: { title: string; progress: number }) {
  return (
    <div className="scene-loading" role="status" aria-label={`正在加载${title}`}>
      <span className="scene-loading-title">正在描绘 · {title}</span>
      <Road progress={progress} tips={SCENE_TIPS} interval={2200}/>
    </div>
  );
}

/** Portrait phones get a rotate invitation; the painted stage is landscape-first. */
export function RotateHint() {
  const [dismissed, setDismissed] = useState(() => localStorage.getItem(ROTATE_KEY) === '1');
  const [portrait, setPortrait] = useState(() => matchMedia('(orientation: portrait) and (max-width: 820px)').matches);
  useEffect(() => {
    const query = matchMedia('(orientation: portrait) and (max-width: 820px)');
    const onChange = () => setPortrait(query.matches);
    query.addEventListener('change', onChange);
    return () => query.removeEventListener('change', onChange);
  }, []);
  if (dismissed || !portrait) return null;
  return (
    <div className="rotate-hint" role="dialog" aria-modal="true" aria-label="建议横屏浏览">
      <div className="rotate-phone" aria-hidden="true"><span /></div>
      <img className="rotate-chibi" src={artImage('daiyu-chibi')} alt="" />
      <h2>横屏进入荣国府</h2>
      <p>等距地图舞台宽更适宜，将手机横置<br/>可以看清每一步行动与院落方位</p>
      <button className="next-button" onClick={() => { localStorage.setItem(ROTATE_KEY, '1'); setDismissed(true); }}>仍要竖屏浏览</button>
    </div>
  );
}
