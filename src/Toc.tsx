import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { chapters } from './story.ts';
import { buildToc, searchToc, type TocEntry, type TocSection } from './toc.ts';

export type { TocEntry, TocSection, TocBook } from './toc.ts';
export { buildToc, tocMark } from './toc.ts';

/** The table of contents.
 *
 *  The header used to carry a native <select> with all 51 sections in it. On a phone
 *  that meant scrolling a 51-item list to reach the sixth book, and there was no way
 *  to search. This is a real index instead: books down the side with their progress,
 *  the sections of the selected book as cards, and a search box that reaches every
 *  book at once.
 *
 *  Three rules the panel has to keep, all of them learned by measurement:
 *
 *  - The book column scrolls on its own. The dialog used to carry the scrolling
 *    (it had only a `max-height`, so the flex chain never got a definite height and
 *    both columns were stretched to their content instead), which meant the reader
 *    could not walk the list of books without dragging the whole panel.
 *  - The chosen book is never out of sight: its heading stays at the top of the
 *    section column while the reader walks the list, and a bar at the bottom of
 *    the panel names the book outright.
 *  - The heading hands over rather than piles up. When a search matches fifteen
 *    books, only the one being read stays pinned; the one above it slides away
 *    as the next arrives. */
export function Toc({ readLog, current, onPick }: {
  readLog: Iterable<string>;
  current: string;
  onPick: (section: TocSection) => void;
}) {
  const { books } = useMemo(() => buildToc(readLog), [readLog]);
  const [activeBook, setActiveBook] = useState<number>(() => {
    const here = chapters.find(section => section.id === current);
    return (here as { book?: number } | undefined)?.book ?? 1;
  });
  const [query, setQuery] = useState('');
  const searchRef = useRef<HTMLInputElement>(null);
  const sectionsRef = useRef<HTMLDivElement>(null);

  // Follow the story only when the story itself moves. The reader's own choice of book
  // has to survive a search: picking the sixth book, searching, then clearing the
  // search must leave the sixth book on screen, not snap back to the current one.
  const lastCurrent = useRef(current);
  useEffect(() => {
    if (lastCurrent.current === current) return;
    lastCurrent.current = current;
    const here = chapters.find(section => section.id === current);
    const book = (here as { book?: number } | undefined)?.book;
    if (book) setActiveBook(book);
  }, [current]);

  useEffect(() => { searchRef.current?.focus(); }, []);

  const needle = query.trim();
  const hits = useMemo(() => (needle ? searchToc(books, needle) : null), [books, needle]);
  const visible = hits ?? books.filter(group => group.book === activeBook).map(group => ({ book: group.book, entries: group.sections }));
  const totalRead = books.reduce((sum, group) => sum + group.read, 0);
  const totalAll = books.reduce((sum, group) => sum + group.total, 0);

  // The bottom bar answers 「现在选的是哪一回」in words. It is the only place that
  // survives every scroll position, so it has to be right even when the heading
  // at the top of the column is off screen.
  const selected = books.find(group => group.book === activeBook);
  const selectedDone = selected?.total ? Math.round(selected.read / selected.total * 100) : 0;
  const hitSections = visible.reduce((sum, group) => sum + group.entries.length, 0);

  /** Bring the paragraph the reader is actually in back into view.
   *
   *  Scrolling the section column is `overflow` on the column itself, so the
   *  offset is measured against the column rather than the window — otherwise the
   *  browser would scroll the dialog too and the column would not move. */
  const jumpToCurrent = useCallback((smooth = false) => {
    const root = sectionsRef.current;
    if (!root) return;
    const card = root.querySelector<HTMLElement>('.toc-card.current');
    if (!card) return;
    const top = card.offsetTop - (root.clientHeight - card.offsetHeight) / 2;
    root.scrollTo({ top: Math.max(0, top), behavior: smooth ? 'smooth' : 'auto' });
  }, []);

  // Changing book replaces the whole section column, which parks the reader at the
  // top of a list they did not ask for. Put the paragraph they are in back in sight.
  useEffect(() => {
    if (needle) return;
    jumpToCurrent();
  }, [activeBook, needle, jumpToCurrent]);

  // The book heading that stays on screen while the reader walks the list.
  //
  //  `position:sticky` was tried first and cannot do this job:
  //
  //  - Its containing block is the nearest block-level ancestor of the scrolling
  //    box. That was `.toc-group`, so the heading was carried off screen together
  //    with its own group and never stuck at all.
  //  - `display:contents` on the group dissolves the wrapper and fixes that, but
  //    then every heading that has crossed the top is pinned at the same offset,
  //    all of them on top of each other (measured: three headings at exactly the
  //    same y). Sticky has no hand-over.
  //
  //  So the heading is placed by script. It is taken out of the flow
  //  (`position:absolute`) and its position is recomputed on every scroll.
  //
  //  The measurement that makes it work: the heading is out of the flow, so its
  //  own bounding box reports where the script last put it, not where the flow
  //  would have put it. The place in the flow is therefore read from the
  //  `.toc-group-slot` that stands in for it — the slot is still a normal in-flow
  //  block, so its box is the honest answer. (`offsetTop` is no use either: with
  //  the group dissolved the offset parent is the dialog, so every heading
  //  reports the same offset and they cannot be told apart.)
  useEffect(() => {
    const root = sectionsRef.current;
    if (!root) return;

    type Head = { el: HTMLElement; top: number; height: number };
    let heads: Head[] = [];

    /** Read where each heading would sit in the flow.
     *
     *  The position is kept in *content* coordinates — the distance from the
     *  column's scroll origin. An absolutely positioned child of the column is
     *  placed with `top` in exactly those coordinates, and the slot's box gives
     *  the honest answer: it is still a normal in-flow block.
     *
     *  The slot is found as the heading's next sibling, not by searching the
     *  parent: the group is `display:contents`, so it generates no box and the
     *  heading's parent is the column itself — a search there would hand every
     *  heading the same first slot. */
    const measure = () => {
      const rootTop = root.getBoundingClientRect().top;
      const scroll = root.scrollTop;
      heads = [...root.querySelectorAll<HTMLElement>('.toc-group-head')].map(el => {
        const slot = el.nextElementSibling as HTMLElement | null;
        const box = slot?.classList.contains('toc-group-slot') ? slot : el;
        return { el, top: box.getBoundingClientRect().top - rootTop + scroll, height: box.offsetHeight };
      });
      place();
    };

    const place = () => {
      if (!heads.length) return;
      const scroll = root.scrollTop;
      // The rail, in content coordinates: the top of the column's content area.
      // A heading pinned at the rail keeps the same `top` value however far the
      // column is scrolled.
      const rail = parseFloat(getComputedStyle(root).paddingTop || '0');
      // The heading the reader is in: the *last* one whose top has reached the
      // rail — the group whose cards are filling the column right now.
      //
      //  Judging by the top rather than the bottom is what makes the hand-over
      // happen at the right moment: as soon as the next heading's top touches
      // the rail, it starts pushing the previous one out.
      let active = -1;
      for (let i = 0; i < heads.length; i++) {
        if (heads[i].top <= rail + scroll) active = i;
      }

      // The active heading holds the rail. Every heading above it has already
      // been passed by, so it is on its way out: it slides up until its bottom
      // meets the top of the one below, and the one above that until it meets
      // that one. The reader sees one heading handing over to the next, never a
      // pile.
      //
      //  `rendered` is in content coordinates, the same ones `top` is measured in
      //  for an absolutely positioned child of the scrolling column. A heading
      //  pinned at the rail therefore has to keep `top` equal to the scroll
      //  position plus the rail — measured, a `top` of the rail alone would put
      //  the heading the same distance above the column as the scroll distance.
      const rendered = new Array<number>(heads.length);
      for (let index = heads.length - 1; index >= 0; index--) {
        if (index > active) { rendered[index] = heads[index].top; continue; }   // not reached yet
        if (index === active) {
          // Holds the rail — but yields upward the moment the next heading,
          // still scrolling up on its own, would overlap it. The approaching
          // heading keeps its natural pace; the passed one slides out edge to
          // edge to meet it. A heading that holds the rail through the whole
          // approach is what piles the two up: the collision zone is the last
          // `height` pixels before the next heading reaches the rail.
          const next = index + 1 < heads.length ? heads[index + 1].top : Infinity;
          rendered[index] = Math.min(rail + scroll, next - heads[index].height);
          continue;
        }
        // Already passed: stack it flush above the heading below it. It ends up
        // off the top of the column, which is exactly where a heading that has
        // been left behind belongs.
        rendered[index] = rendered[index + 1] - heads[index].height;
      }
      heads.forEach((head, index) => { head.el.style.top = `${rendered[index]}px`; });
    };

    measure();
    root.addEventListener('scroll', place, { passive: true });
    window.addEventListener('resize', measure);
    // The groups change when the search changes, and the cards change height with
    // the text they carry; both move the headings' natural positions.
    const observer = new ResizeObserver(measure);
    observer.observe(root);
    return () => {
      root.removeEventListener('scroll', place);
      window.removeEventListener('resize', measure);
      observer.disconnect();
    };
  }, [needle, activeBook]);

  // Which book the reader is looking at right now. In a search across fifteen
  // books the bottom bar follows the scroll, so it always names the book the
  // reader is actually in rather than the one the search started from.
  const [liveBook, setLiveBook] = useState<number | null>(null);
  useEffect(() => {
    const root = sectionsRef.current;
    if (!root) return;
    let frame = 0;
    const update = () => {
      frame = 0;
      const heads = [...root.querySelectorAll<HTMLElement>('.toc-group-head')];
      if (!heads.length) { setLiveBook(null); return; }
      const rootTop = root.getBoundingClientRect().top;
      const rail = rootTop + parseFloat(getComputedStyle(root).paddingTop || '0');
      let found: number | null = null;
      for (const head of heads) {
        // The group the reader is in is the last one whose heading has gone by.
        const box = head.getBoundingClientRect();
        if (box.bottom <= rail + 1) found = Number(head.dataset.book ?? 0) || null;
      }
      setLiveBook(found);
    };
    const onScroll = () => { if (!frame) frame = requestAnimationFrame(update); };
    root.addEventListener('scroll', onScroll, { passive: true });
    update();
    return () => { root.removeEventListener('scroll', onScroll); if (frame) cancelAnimationFrame(frame); };
  }, [needle, activeBook]);

  return <div className="toc-body">
    <div className="toc-top">
      <input ref={searchRef} className="toc-search" type="search" value={query}
        placeholder="搜段落、人物或地点（如「梨香院」「宝钗」「太虚」）"
        aria-label="搜索剧情段落" onChange={event => setQuery(event.target.value)}
        onKeyDown={event=>{
          // A search box eats Escape to clear itself, so the first Escape would leave
          // the panel open with an empty box. Clear the search and keep the panel:
          // the reader who typed a word usually wants to edit it, not to leave.
          // With an empty box, Escape falls through and closes the panel.
          if(event.key==='Escape'&&query){event.preventDefault();event.stopPropagation();setQuery('');}
        }}/>
      <span className="toc-progress" title={`${totalRead} / ${totalAll} 节点`}>
        <strong>{totalAll ? Math.round(totalRead / totalAll * 100) : 0}%</strong>
        <small>已读 {totalRead} / {totalAll}</small>
      </span>
    </div>

    <div className="toc-layout">
      <nav className="toc-books" aria-label="按回目浏览">
        {books.map(group => {
          const done = group.total ? Math.round(group.read / group.total * 100) : 0;
          return <button key={group.book}
            className={`toc-book${!needle && group.book === activeBook ? ' active' : ''}${group.read >= group.total && group.total ? ' done' : ''}`}
            aria-current={!needle && group.book === activeBook ? 'true' : undefined}
            onClick={() => { setQuery(''); setActiveBook(group.book); }}>
            <span className="toc-book-name">{group.name}</span>
            <span className="toc-book-bar"><i style={{ width: `${done}%` }}/></span>
            <span className="toc-book-count">{group.sections.length} 段</span>
          </button>;
        })}
      </nav>

      <div className="toc-sections" ref={sectionsRef}>
        {visible.length === 0 && <p className="toc-empty">没有找到「{needle}」。换个词试试，或只搜地点、人物。</p>}
        {visible.map(group => {
          const meta = books.find(book => book.book === group.book);
          return <section key={group.book} className="toc-group">
            <h3 className="toc-group-head" data-book={group.book}>{meta?.name ?? `第${group.book}回`}<small>{group.entries.length} 段</small></h3>
            {/* 标题被绝对定位摘出了文档流，这个空位替它留在原处。 */}
            <div className="toc-group-slot" aria-hidden="true"/>
            <div className="toc-grid">
              {group.entries.map(entry => <button key={entry.id}
                className={`toc-card${entry.id === current ? ' current' : ''}${entry.read >= entry.total && entry.total ? ' read' : ''}`}
                data-section={entry.id}
                aria-current={entry.id === current ? 'true' : undefined}
                aria-label={`${meta?.name ?? ''} · ${entry.title}${entry.place ? ' · ' + entry.place : ''}${entry.actors.length ? ' · ' + entry.actors.join('、') : ''}`}
                onClick={() => onPick(entry)}>
                <span className="toc-card-mark" aria-hidden="true">{entry.mark}</span>
                <strong>{entry.title}</strong>
                <small className="toc-card-place" title={entry.places.join(' / ')}>
                  {entry.places.length > 1 ? `${entry.places[0]} 等 ${entry.places.length} 处` : entry.places[0]}
                </small>
                {entry.actors.length > 0 && <small className="toc-card-actors" title={entry.actors.join('、')}>
                  {entry.actors.length > 4 ? `${entry.actors.slice(0, 4).join('、')} 等 ${entry.actors.length} 人` : entry.actors.join('、')}
                </small>}
                <span className="toc-card-bar"><i style={{ width: `${entry.total ? Math.round(entry.read / entry.total * 100) : 0}%` }}/></span>
              </button>)}
            </div>
          </section>;
        })}
      </div>
    </div>

    {/* 吸底：面板最下面那一行。它不随任何一栏滚动，所以「选的是哪一回」
        永远有一处白纸黑字写着，不靠读者记住刚才点过哪里。
        搜索跨回时，这一行跟着滚动位置改写：它报的是读者此刻正在看的那一回。 */}
    <div className="toc-foot">
      <span className="toc-foot-label">{needle ? '正在看' : '所选回目'}</span>
      <strong className="toc-foot-name">{needle
        ? (liveBook ? (books.find(b => b.book === liveBook)?.name ?? `第${liveBook}回`) : `「${needle}」`)
        : (selected?.name ?? `第${activeBook}回`)}</strong>
      <span className="toc-foot-meta">{needle
        ? `命中 ${visible.length} 回 · ${hitSections} 段`
        : `${selected?.sections.length ?? 0} 段 · 已读 ${selected?.read ?? 0}/${selected?.total ?? 0}`}</span>
      {!needle && <span className="toc-foot-bar" aria-hidden="true"><i style={{ width: `${selectedDone}%` }}/></span>}
      <button className="toc-foot-jump" disabled={!!needle}
        title={needle ? '清空搜索后可回到当前段落' : '把正在读的那一段滚回视野'}
        onClick={() => jumpToCurrent(true)}>回到当前段</button>
    </div>
  </div>;
}
