import assert from 'node:assert/strict';
import { test } from 'node:test';
import { cnNumber } from '../src/cnNumber.ts';

test('中文数字：一位与十位', () => {
  assert.equal(cnNumber(0), '零');
  assert.equal(cnNumber(1), '一');
  assert.equal(cnNumber(9), '九');
  assert.equal(cnNumber(10), '十');
  assert.equal(cnNumber(11), '十一');
  assert.equal(cnNumber(19), '十九');
  assert.equal(cnNumber(20), '二十');
  assert.equal(cnNumber(22), '二十二');
  assert.equal(cnNumber(25), '二十五');
  assert.equal(cnNumber(30), '三十');
  assert.equal(cnNumber(99), '九十九');
});

test('中文数字：百位补位不丢「一」', () => {
  assert.equal(cnNumber(100), '一百');
  assert.equal(cnNumber(101), '一百零一');
  assert.equal(cnNumber(110), '一百一十');
  assert.equal(cnNumber(115), '一百一十五');
  assert.equal(cnNumber(120), '一百二十');
  assert.equal(cnNumber(199), '一百九十九');
  assert.equal(cnNumber(200), '二百');
});

test('中文数字：千位与万位', () => {
  assert.equal(cnNumber(1000), '一千');
  assert.equal(cnNumber(1001), '一千零一');
  assert.equal(cnNumber(1010), '一千零一十');
  assert.equal(cnNumber(1100), '一千一百');
  assert.equal(cnNumber(10000), '一万');
  assert.equal(cnNumber(10001), '一万零一');
  assert.equal(cnNumber(10010), '一万零一十');
  assert.equal(cnNumber(10086), '一万零八十六');
});

test('中文数字：亿位与整组零', () => {
  assert.equal(cnNumber(100000000), '一亿');
  assert.equal(cnNumber(100010000), '一亿零一万');
  assert.equal(cnNumber(100000001), '一亿零一');
  assert.equal(cnNumber(120000000), '一亿二千万');
});

test('中文数字：非法输入退回原样', () => {
  assert.equal(cnNumber(NaN), 'NaN');
  assert.equal(cnNumber(Infinity), 'Infinity');
  assert.equal(cnNumber(-5), '负五');
});

test('中文数字：与回数写法一致（面板标题用）', () => {
  // 面板标题「前 N 回」历史上写成「前二十二回」，这里钉住它。
  assert.equal(cnNumber(22), '二十二');
  assert.equal(cnNumber(15), '十五');
  assert.equal(cnNumber(4), '四');
});
