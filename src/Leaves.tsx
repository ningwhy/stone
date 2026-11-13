import { useMemo } from 'react';
import { cast, bookNames } from './story.ts';
import type { ActorId } from './story.ts';
import { chapterLeaf, chapterTitle } from './leaves.ts';
import { Portrait } from './Portrait.tsx';

/** The cover and the back cover of a book.
 *
 *  A chapter of a 《红楼梦》 is a small book of its own: a title page in front
 *  and 「本回完」 behind. This is that rhythm, made of the story's own material:
 *
 *  - the cover carries the title couplet of the chapter and the people who
 *    actually walk on stage during it, drawn from the node actions rather than
 *    written by hand, so it cannot drift from the story;
 *  - the back cover closes the chapter and names the one that follows, and the
 *    reader turns the page themselves.
 *
 *  The page is a sheet laid over the stage, not a panel that replaces it: the
 *  map is still there underneath, so the reader sees the chapter about to
 *  begin rather than an interruption. */

export type LeafKind = 'cover' | 'back';

/** The people on the cover, with the portrait of each.
 *
 *  The cover of a printed book lists names; this one can show a face, which is
 *  what the reader of an illustrated edition expects. A chapter with forty
 *  people on stage cannot show forty faces, so the first few carry a portrait
 *  and the rest are named in a line. */
function CoverCast({ actors }: { actors: string[] }) {
  // The cast table is keyed by id, but the leaf carries reader-facing names, so
  // the id is found by name — the same way the table of contents does it.
  const byName = useMemo(() => {
    const map = new Map<string, ActorId>();
    for (const [id, person] of Object.entries(cast)) map.set(person.name, id as ActorId);
    return map;
  }, []);
  const shown = actors.slice(0, 8).map(name => byName.get(name)).filter(Boolean) as ActorId[];
  const rest = actors.slice(8);
  if (!actors.length) return null;
  return <>
    <ul className="leaf-cast">
      {shown.map(id => <li key={id}>
        <span className="leaf-cast-face"><Portrait actor={id} face="right"/></span>
        <span>{cast[id].name}</span>
      </li>)}
    </ul>
    {rest.length > 0 && <p className="leaf-cast-rest">另有 {rest.join('、')}</p>}
  </>;
}

/** The cover: the title couplet of the chapter and who is in it. */
export function ChapterCover({ book, onOpen }: { book: number; onOpen: () => void }) {
  const title = chapterTitle(book);
  const leaf = chapterLeaf(book);
  if (!title || !leaf) return null;
  return <section className="leaf-sheet leaf-cover" role="dialog" aria-modal="true" aria-label={`${bookNames[book]} 封面`}>
    <div className="leaf-inner">
      <p className="leaf-book">{bookNames[book]}</p>
      <h2 className="leaf-title">
        <span>{title.first}</span>
        <span>{title.second}</span>
      </h2>
      <p className="leaf-rule" aria-hidden="true"><i/><i/></p>
      {leaf.actors.length > 0 && <>
        <p className="leaf-caption">本回人物</p>
        <CoverCast actors={leaf.actors}/>
      </>}
      <button className="leaf-open next-button" onClick={onOpen}>展开本回 <span aria-hidden="true">→</span></button>
    </div>
  </section>;
}

/** The back cover: the chapter is finished, and the next one is named.
 *
 *  The reader turns the page themselves. The next chapter's cover follows, so
 *  a chapter break reads as a book being opened rather than a story that
 *  stopped.
 *
 *  The sheet can also be put away — a reader who wants to look back at the
 *  last lines of the chapter they just finished needs a way back to them. */
export function ChapterBackCover({ book, nextBook, onOpen, onFold }: { book: number; nextBook: number | null; onOpen: () => void; onFold: () => void }) {
  const nextTitle = nextBook != null ? chapterTitle(nextBook) : null;
  return <section className="leaf-sheet leaf-back" role="dialog" aria-modal="true" aria-label={`${bookNames[book]} 封底`}>
    <div className="leaf-inner">
      <p className="leaf-book">本回目完</p>
      <h2 className="leaf-title leaf-title-end">
        <span>{bookNames[book]}</span>
        <span>已读完</span>
      </h2>
      <p className="leaf-rule" aria-hidden="true"><i/><i/></p>
      {nextBook != null && nextTitle
        ? <div className="leaf-next">
            <p className="leaf-caption">下一回</p>
            <p className="leaf-next-name">{bookNames[nextBook]}</p>
            <p className="leaf-next-title">{nextTitle.first}<br/>{nextTitle.second}</p>
            <button className="leaf-open next-button" onClick={onOpen}>开启下一回 <span aria-hidden="true">→</span></button>
          </div>
        : <p className="leaf-next-title leaf-final">全书至此，砖石犹温。</p>}
      {/* 收起封底走的是自己的回调，不再派发 Escape：Escape 有两个处理器
          （封底折叠与全局翻页），派发事件会让两边都听见。 */}
      <button className="leaf-fold" onClick={onFold}>收起封底，回看本回</button>
    </div>
  </section>;
}
