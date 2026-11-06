import titles from '../design/chapter-titles.json' with { type: 'json' };
import { cast, chapters, story } from './story.ts';
import { nodeActors } from './toc.ts';

/** The two leaves of a book: the cover in front of a chapter and the back cover
 *  behind it.
 *
 *  A chapter of a Chinese novel is a small book of its own. It opens with a
 *  title page — the couplet that names the whole chapter in half a dozen
 *  words — and it closes with 「本回完」 before the next one is bound. The
 *  reader of a 《红楼梦》 app expects that rhythm: without it a chapter runs
 *  straight into the next one and the book never seems to turn a page.
 *
 *  The two leaves are built from the story itself rather than written by hand:
 *  the people on the cover are the ones who actually walk on stage during that
 *  chapter, and the back cover names the chapter that comes next. A hand-written
 *  list would drift the moment a node changed. */

/** The title couplet of one book, as its own front page carries it. */
export type ChapterTitle = { first: string; second: string };

const titleTable = titles.books as Record<string, ChapterTitle>;

export function chapterTitle(book: number): ChapterTitle | null {
  return titleTable[String(book)] ?? null;
}

/** Where one book begins and ends in the story, and who is on stage in it.
 *
 *  The people are collected from the same source the table of contents uses —
 *  the actions of every node — so the cover lists exactly who walks on stage,
 *  in order of first appearance. */
export type ChapterLeaf = {
  book: number;
  /** The node the chapter opens with and the node it closes on. */
  firstNode: string;
  lastNode: string;
  /** Everyone on stage during the chapter, by reader-facing name, in order of
   *  first appearance. */
  actors: string[];
  /** How many nodes the chapter holds. */
  nodes: number;
};

let cache: Map<number, ChapterLeaf> | null = null;

/** The leaves of every book, computed once. */
export function chapterLeaves(): Map<number, ChapterLeaf> {
  if (cache) return cache;
  const byBook = new Map<number, ChapterLeaf>();
  // The nodes of a chapter are the ones whose section belongs to it. A section
  // carries the book it belongs to, so the book of a node is the book of the
  // section that holds it.
  const bookOfSection = new Map<string, number>();
  for (const section of chapters) bookOfSection.set(section.id, (section as { book: number }).book);

  const nodesByBook = new Map<number, typeof story>();
  for (const node of story) {
    const book = bookOfSection.get(node.chapter);
    if (book == null) continue;
    const bucket = nodesByBook.get(book) ?? [];
    bucket.push(node);
    nodesByBook.set(book, bucket);
  }

  for (const [book, nodes] of nodesByBook) {
    if (!nodes.length) continue;
    const actors: string[] = [];
    for (const node of nodes) {
      for (const id of nodeActors(node)) {
        const name = cast[id as keyof typeof cast]?.name ?? id;
        if (!actors.includes(name)) actors.push(name);
      }
    }
    byBook.set(book, {
      book,
      firstNode: nodes[0].id,
      lastNode: nodes[nodes.length - 1].id,
      actors,
      nodes: nodes.length,
    });
  }
  cache = byBook;
  return byBook;
}

export function chapterLeaf(book: number): ChapterLeaf | null {
  return chapterLeaves().get(book) ?? null;
}

/** Which leaf the reader is about to be shown.
 *
 *  A chapter turns its own pages: the cover comes when the chapter opens, the
 *  back cover when it closes. Both are decided by the node the reader is on,
 *  not by how many nodes they have read — the node id is the one mark that
 *  cannot lie, because seeking back and restoring a save both break a count.
 *
 *  Only a natural step turns the page. Jumping in the index lands on the same
 *  nodes, but a reader who seeks is looking for a scene, not turning a page,
 *  and a back cover would drag them away from where they meant to go.
 *
 *  `advanced` says the reader moved on by one step. `atStart` says they opened
 *  the book at the very beginning — the first chapter has no previous step to
 *  have advanced from, so its cover still deserves to show. */
export type LeafTrigger = 'cover' | 'back' | null;

/** Decide which leaf, if any, the given position calls for. */
export function leafTrigger(input: {
  /** The node the reader is on. */
  nodeId: string;
  /** The leaves of the chapter that node belongs to. */
  leaf: ChapterLeaf | null;
  /** Did the reader move forward by exactly one step? */
  advanced: boolean;
  /** Are they at the very first node of the book? */
  atStart: boolean;
}): LeafTrigger {
  const { nodeId, leaf, advanced, atStart } = input;
  if (!leaf) return null;
  if (nodeId === leaf.lastNode) return advanced ? 'back' : null;
  if (nodeId === leaf.firstNode) return advanced || atStart ? 'cover' : null;
  return null;
}
