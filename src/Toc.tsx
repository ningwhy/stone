import { useEffect, useMemo, useRef, useState } from 'react';
import { chapters } from './story.ts';
import { buildToc, searchToc, type TocSection } from './toc.ts';

export type { TocEntry, TocSection, TocBook } from './toc.ts';
export { buildToc, tocMark } from './toc.ts';

/** The table of contents.
 *
 *  The header used to carry a native <select> with all 51 sections in it. On a phone
 *  that meant scrolling a 51-item list to reach the sixth book, and there was no way
 *  to search. This is a real index instead: books down the side with their progress,
 *  the sections of the selected book as cards, and a search box that reaches every
 *  book at once. */
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

      <div className="toc-sections">
        {visible.length === 0 && <p className="toc-empty">没有找到「{needle}」。换个词试试，或只搜地点、人物。</p>}
        {visible.map(group => {
          const meta = books.find(book => book.book === group.book);
          return <section key={group.book} className="toc-group">
            <h3>{meta?.name ?? `第${group.book}回`}<small>{group.entries.length} 段</small></h3>
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
  </div>;
}
