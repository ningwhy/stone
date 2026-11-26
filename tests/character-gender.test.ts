import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

// 门禁：每个角色的提示词必须显式锚定性别。
//
// 起因：第 26-30 回的司棋因为提示词里没有性别词，被 qwen21 画成了男性青年。
// 事后逐个复核 89 个角色的立绘与 Q 版，发现蒋玉菡同样出问题——底本第二十八回
// 明写他是「唱小旦的蒋玉菡」（男优伶扮旦角），却被画成粉衣女子。
//
// 因此这里把「提示词必须锚定性别」固化成自动断言：
//   1. character-designs.json 里每个角色 prompt 都带 WOMAN/GIRL/FEMALE/MAN/MALE/BOY；
//   2. 每个角色 features 都写明性别与底本依据；
//   3. manifest 里每条 identity.features 与设计表逐字一致（四处同步的证据）。

const designs = JSON.parse(
  readFileSync(new URL('../art/identity/character-designs.json', import.meta.url), 'utf8'),
);
const manifest = JSON.parse(
  readFileSync(new URL('../public/assets/rongguo/manifest.json', import.meta.url), 'utf8'),
);

const ANCHOR = /\b(WOMAN|GIRL|FEMALE|MAN|MALE|BOY)\b/;
const featuresById = new Map<string, string>(
  designs.characters.map((c: { id: string; features: string }) => [c.id, c.features]),
);

test('every character prompt anchors its gender', () => {
  const missing: string[] = [];
  for (const c of designs.characters) {
    if (!ANCHOR.test(c.prompt)) missing.push(c.id);
  }
  assert.deepEqual(missing, [], `这些角色的提示词没有性别锚定：${missing.join(', ')}`);
});

test('every character records its gender and the source-text evidence', () => {
  const missing: string[] = [];
  const noEvidence: string[] = [];
  for (const c of designs.characters) {
    if (!c.features.includes('性别：')) missing.push(c.id);
    // 性别依据必须引用底本：至少一个「第N回」标记
    else if (!/第[一二三四五六七八九十\d]+回/.test(c.features)) noEvidence.push(c.id);
  }
  assert.deepEqual(missing, [], `这些角色没写性别：${missing.join(', ')}`);
  assert.deepEqual(noEvidence, [], `这些角色的性别没有底本依据：${noEvidence.join(', ')}`);
});

test('manifest identity features match the design table verbatim', () => {
  const drifted: string[] = [];
  let checked = 0;
  for (const [key, val] of Object.entries<any>(manifest.assets)) {
    const ident = val?.identity;
    if (!ident || !ident.features) continue;
    const expected = featuresById.get(ident.character);
    if (expected === undefined) continue;
    checked++;
    if (ident.features !== expected) drifted.push(key);
  }
  assert.ok(checked > 0, 'manifest 里应当至少有一条带 features 的身份记录');
  assert.deepEqual(drifted, [], `manifest 与设计表的 features 不一致：${drifted.join(', ')}`);
});

test('gender anchors agree with the declared sex in features', () => {
  // 提示词里出现 WOMAN/GIRL/FEMALE 的角色，features 必须写「性别：女」；
  // 出现 MAN/MALE/BOY 的必须写「性别：男」。两处打架说明改了一处忘了另一处。
  const conflicts: string[] = [];
  for (const c of designs.characters) {
    const female = /\b(WOMAN|GIRL|FEMALE)\b/.test(c.prompt);
    const male = /\b(MAN|MALE|BOY)\b/.test(c.prompt);
    if (female == male) {
      conflicts.push(`${c.id}: 提示词性别锚不唯一`);
      continue;
    }
    const declared = /性别：([男女])/.exec(c.features)?.[1];
    if (declared === undefined) continue;
    const expect = female ? '女' : '男';
    if (declared !== expect) conflicts.push(`${c.id}: 提示词锚=${expect} 但 features 写「${declared}」`);
  }
  assert.deepEqual(conflicts, [], conflicts.join('; '));
});
