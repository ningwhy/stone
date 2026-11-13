/** 整数写成中文数字：二十二、一百零三、一千零一十。
 *
 *  面板标题上的「前 N 回」要跟着实际回数走。这句话曾经是用一张查表算的，
 *  查表有个上限：上限一满就得回去加一条，加漏了标题上就露出阿拉伯数字
 *  （写着「前22回 · 人物图鉴」）。回数会一直往上加，所以这里按位算，
 *  不设上限。
 *
 *  写法上踩过两次坑，两次都不是查表能挡住的：
 *  1. 递归补位（「一百」+「十」）在 110 上漏掉补位的「一」，
 *     写成「一百十」；在 1010 上又把十位的「一」吃掉，写成「一千零十」。
 *  2. 「零」什么时候该出现、什么时候不该出现，规则是
 *     「有非零位被零位隔开才插零」，而不是「小于阈值就插零」——
 *     末尾的零不插（100 是「一百」不是「一百零」），同一组内的零也不插
 *     （110 是「一百一十」不是「一百零一十」）。
 *
 *  现在的做法：按四位一组从高到低扫，组内用「pending 零」标记，组间
 *  低位组不足千位且高位组非空时补一个「零」。 */
const DIGITS = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九'];
/** 组内进位单位，**高位在前**：千、百、十、（无）。 */
const UNITS = ['千', '百', '十', ''];
/** 四位组之上的进位单位：万、亿、万亿…… */
const GROUP_UNITS = ['', '万', '亿', '万亿'];

/** 一组（1..9999）的中文写法。 */
function under10000(n: number): string {
  const digits = [
    Math.floor(n / 1000) % 10,
    Math.floor(n / 100) % 10,
    Math.floor(n / 10) % 10,
    n % 10,
  ];
  let out = '';
  let written = false;
  let pendingZero = false;
  for (let i = 0; i < 4; i++) {
    const v = digits[i];
    if (v === 0) {
      // 末尾的零不插零（100 是「一百」）；组首的零直接跳过（007 是「七」）。
      if (written) pendingZero = true;
      continue;
    }
    if (pendingZero) {
      out += '零';
      pendingZero = false;
    }
    out += DIGITS[v] + UNITS[i];
    written = true;
  }
  return out;
}

/** 整数转中文数字。不设上限，回数一直加也不会退化。 */
export function cnNumber(n: number): string {
  if (!Number.isFinite(n)) return String(n);
  const negative = n < 0;
  let rest = Math.floor(Math.abs(n));
  if (rest === 0) return '零';

  const groups: number[] = [];
  while (rest > 0) {
    groups.push(rest % 10000);
    rest = Math.floor(rest / 10000);
  }

  let out = '';
  let pendingZero = false;
  for (let i = groups.length - 1; i >= 0; i--) {
    const g = groups[i];
    if (g === 0) {
      // 中间整组为零且下面还有非零组，要留一个「零」（一亿零一万零一）。
      if (i > 0 && groups.slice(0, i).some(v => v !== 0)) pendingZero = true;
      continue;
    }
    let piece = under10000(g);
    if (i > 0) piece += GROUP_UNITS[i] ?? '';
    if (pendingZero) {
      out += '零';
      pendingZero = false;
    } else if (out && g < 1000) {
      // 低位组不足千位，与高位组之间空着整段（10001 是「一万零一」）。
      out += '零';
    }
    out += piece;
  }

  // 整数只有十几时读作「十/十一/十九」，不带一十的一。
  if (out.startsWith('一十')) out = out.slice(1);
  return negative ? '负' + out : out;
}
