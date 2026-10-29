import { cast, chapters, bookNames, story } from './story.ts';

/** One section (段落) as the table of contents sees it. */
export type TocSection = {
  id: string; title: string; book: number; scene: string; start: string;
  /** How much of this section the reader has been through: 0 = untouched, 1 = finished. */
  read: number; total: number; place: string;
  /** Every place the section passes through, in reading order. A section often crosses
   *  several (碧纱橱 → 穿堂 → 荣禧堂), and the card should be findable by any of them. */
  places: string[];
  /** The people who are actually on stage in this section, in order of first appearance. */
  actors: string[];
};

export type TocEntry = TocSection & {
  mark: string;
  /** Everything searchable in this section, precomputed: the title, its places, its
   *  people and its spoken text. Searching this one string keeps a keystroke from
   *  rescanning the whole story. */
  haystack: string;
};

export type TocBook = {
  book: number; name: string; sections: TocEntry[]; read: number; total: number;
};

/** Read marks: ○ 未读 · ◐ 读了一部分 · ● 读完. Same glyphs the old dropdown used,
 *  so a reader who learned one learns the other. */
export function tocMark(read: number, total: number): string {
  if (read === 0) return '○';
  if (read >= total) return '●';
  return '◐';
}

/** Everyone who is on stage in one node: walked in, shown, or speaks.
 *
 *  The actions are the only record of who is present — the cast table says who
 *  exists in the book, not who is in this room. A person who is only talked
 *  about is deliberately left out: the reader wants the paragraph where they
 *  appear, not the one that mentions them in passing. */
export function nodeActors(step: { actions: readonly unknown[]; speaker: string }): string[] {
  const out: string[] = [];
  const push = (actor: string) => { if (actor && actor !== 'narrator' && !out.includes(actor)) out.push(actor); };
  for (const action of step.actions as readonly { type: string; actor?: string; moves?: { actor: string }[] }[]) {
    if (action.type === 'move' || action.type === 'show' || action.type === 'effect') push(action.actor ?? '');
    else if (action.type === 'parallel') for (const move of action.moves ?? []) push(move.actor);
  }
  push(step.speaker);
  return out;
}

/** The reader-facing names of a section's people, each with its full name too, so
 *  that 「王夫人」 and 「王夫人」 by full name both find the same paragraph. */
function actorSearchText(names: string[]): string {
  return names.flatMap(name => {
    const actor = Object.values(cast).find(candidate => candidate.name === name);
    return actor ? [actor.name, actor.fullName] : [name];
  }).join(' ');
}

/** Group the sections by book, in reading order, with their progress.
 *  `readLog` is the set of node ids the reader has actually reached. */
export function buildToc(readLog: Iterable<string>): { books: TocBook[] } {
  const read = new Set(readLog);
  const byBook = new Map<number, TocEntry[]>();
  for (const section of chapters) {
    const nodes = story.filter(node => node.chapter === section.id);
    const done = nodes.filter(node => read.has(node.id)).length;

    // Every place the section passes through, in reading order — the first node's
    // place alone would hide the second half of a section that crosses two rooms.
    const places: string[] = [];
    for (const node of nodes) {
      for (const piece of node.place.split(' / ')) {
        const place = piece.trim();
        if (place && !places.includes(place)) places.push(place);
      }
    }

    // Everyone on stage, in order of first appearance, by their reader-facing name.
    const actors: string[] = [];
    for (const node of nodes) {
      for (const actor of nodeActors(node)) {
        const name = cast[actor as keyof typeof cast]?.name ?? actor;
        if (!actors.includes(name)) actors.push(name);
      }
    }

    const entry: TocEntry = {
      id: section.id, title: section.title, book: (section as { book: number }).book,
      scene: section.scene, start: section.start,
      read: done, total: nodes.length,
      place: places[0] ?? '',
      places, actors,
      mark: tocMark(done, nodes.length),
      haystack: '',
    };
    // The spoken text of the section is searchable too, so that a word taken
    // straight from the book finds its paragraph even when no title carries it.
    entry.haystack = searchText(entry, bookNames[entry.book] ?? `第${entry.book}回`,
      nodes.map(node => `${node.title} ${node.text}`).join(' '));
    const bucket = byBook.get(entry.book) ?? [];
    bucket.push(entry);
    byBook.set(entry.book, bucket);
  }
  const books = [...byBook.entries()].sort((a, b) => a[0] - b[0]).map(([book, sections]) => ({
    book, name: bookNames[book] ?? `第${book}回`, sections,
    read: sections.reduce((sum, section) => sum + section.read, 0),
    total: sections.reduce((sum, section) => sum + section.total, 0),
  }));
  return { books };
}

/** Everything a reader might type to find this section, in one string.
 *
 *  The search box promises 「搜段落、人物或地点」, so all three have to be in here:
 *  the title, every place the section passes through, every person on stage (by
 *  short name and by full name), and the words actually spoken in it. */
export function searchText(entry: TocEntry, bookName: string, spoken: string): string {
  return `${entry.title} ${entry.places.join(' ')} ${actorSearchText(entry.actors)} ${spoken} ${bookName} ${entry.id}`;
}

/** The sections a search finds, grouped by book. A search reaches every book at
 *  once — that is the whole point of it: the reader should not have to know which
 *  book a place or a person is in. */
export function searchToc(books: TocBook[], needle: string): { book: number; entries: TocEntry[] }[] {
  const query = needle.trim();
  if (!query) return [];
  const found: { book: number; entries: TocEntry[] }[] = [];
  for (const group of books) {
    const entries = group.sections.filter(entry => entry.haystack.includes(query));
    if (entries.length) found.push({ book: group.book, entries });
  }
  return found;
}
