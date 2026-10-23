import type { StoryStep } from './story.ts';

export type Emotion = 'neutral' | 'joy' | 'sad' | 'surprise' | 'angry';

/** Cue words scored per category; explicit `mood` fields win. Angry outranks sad on ties
 * because 摔玉-style beats carry both. */
const CUES: [Exclude<Emotion,'neutral'>, RegExp][] = [
  ['angry', /怒|恼|斥|骂|嗔|愠|摔|掷|恨|咬牙/g],
  ['sad', /哭|泪|悲|哀|呜|泣|伤心|叹|愁|恸|黯然|含悲|垂泪/g],
  ['surprise', /惊|讶|骇|慌|愕|怔|失色|忙问|急忙/g],
  ['joy', /笑|喜|欢|欣|悦|眉开|含笑/g],
];

/** Which portrait variant the speaker should wear for this node. */
export function emotionOf(step: StoryStep): Emotion {
  if (step.mood === 'sad') return 'sad';
  let best: Emotion = 'neutral', hits = 0;
  for (const [emotion, pattern] of CUES) {
    const count = step.text.match(pattern)?.length ?? 0;
    if (count > hits) { best = emotion; hits = count; }
  }
  return best;
}
