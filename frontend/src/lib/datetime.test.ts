/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

import { describe, expect, it } from 'vitest';
import {
  SUPPORTED_DATE_FORMATS,
  formatByPattern,
  formatDateTime,
  formatEnLongDate,
  formatEnLongDateTime,
  formatIsoDate,
  formatIsoDateTime,
  formatIsoUtc,
  formatJaEraShortYmd,
  formatJaEraYmd,
  formatJaEraYmdHm,
  formatJaKanjiMdHms,
  formatJaKanjiYmdHms,
  formatJaYmd,
  formatJaYmdHm,
  formatJaYmdHms,
  formatJaYmdKanji,
  formatJstDateTime,
  formatUkDate,
  formatUkDateTime,
  formatUsDate,
  formatUsDateTime12,
  formatUsDateTime24,
  normalizeIso,
  toDate,
  type SupportedDateFormat,
} from './datetime';

// Tuesday. 03:04:05.006 UTC == 12:04:05.006 JST. Tests run with TZ=UTC (vitest.config.ts).
const SAMPLE = '2026-02-10T03:04:05.006Z';

const normalizeSpaces = (s: string) => s.replace(/[\u202f\u00a0]/g, ' ');

describe('normalizeIso', () => {
  it.each([
    [null, ''],
    [undefined, ''],
    ['', ''],
    ['   ', ''],
    ['2026-02-10T12:00:00Z', '2026-02-10T12:00:00Z'],
    ['2026-02-10 12:00:00', '2026-02-10T12:00:00'],
    ['  2026-02-10 12:00:00  ', '2026-02-10T12:00:00'],
    ['2026-02-10T12:00:00+0900', '2026-02-10T12:00:00+09:00'],
    ['2026-02-10T12:00:00-0530', '2026-02-10T12:00:00-05:30'],
    ['2026-02-10T12:00:00+09:00', '2026-02-10T12:00:00+09:00'],
    ['2026-02-10T12:00:00.123456', '2026-02-10T12:00:00.123'],
    ['2026-02-10 12:00:00.123456+0900', '2026-02-10T12:00:00.123+09:00'],
    ['2026-02-10', '2026-02-10'],
  ])('normalizeIso(%j) -> %j', (input, expected) => {
    expect(normalizeIso(input)).toBe(expected);
  });
});

describe('toDate', () => {
  it('returns the same Date instance when valid', () => {
    const d = new Date(SAMPLE);
    expect(toDate(d)).toBe(d);
  });

  it('returns null for an invalid Date', () => {
    expect(toDate(new Date('nope'))).toBeNull();
  });

  it.each([null, undefined, '', 'not-a-date'])('returns null for %j', (v) => {
    expect(toDate(v)).toBeNull();
  });

  it('parses Python-style timestamps (space separator, +HHMM offset, microseconds)', () => {
    expect(toDate('2026-02-10 12:04:05.006789+0900')?.toISOString()).toBe(SAMPLE);
  });
});

describe('formatDateTime', () => {
  it('delegates to Intl.DateTimeFormat', () => {
    expect(
      formatDateTime(SAMPLE, 'en-US', { year: 'numeric', timeZone: 'UTC' }),
    ).toBe('2026');
  });

  it('returns an empty string for unparseable input', () => {
    expect(formatDateTime('garbage', 'en-US', {})).toBe('');
  });
});

describe('Japanese (JST) formatters', () => {
  it.each([
    ['formatJaYmd', formatJaYmd, '2026/02/10'],
    ['formatJaYmdKanji', formatJaYmdKanji, '2026年02月10日'],
    ['formatJaYmdHm', formatJaYmdHm, '2026/02/10 12:04'],
    ['formatJaYmdHms', formatJaYmdHms, '2026/02/10 12:04:05'],
    ['formatJaKanjiMdHms', formatJaKanjiMdHms, '02月10日 12時04分05秒'],
    ['formatJaKanjiYmdHms', formatJaKanjiYmdHms, '2026年02月10日 12時04分05秒'],
    ['formatJstDateTime', formatJstDateTime, '2026年02月10日 12時04分05.006秒'],
    ['formatJaEraYmd', formatJaEraYmd, '令和08年02月10日'],
    ['formatJaEraYmdHm', formatJaEraYmdHm, '令和08年02月10日 12時04分'],
  ])('%s', (_name, fn, expected) => {
    expect(fn(SAMPLE)).toBe(expected);
  });

  it('formatJaEraShortYmd uses the short era name from Intl', () => {
    // ICU renders era "short" for ja as the full era name (令和), not "R".
    expect(formatJaEraShortYmd(SAMPLE)).toBe('令和08/02/10');
  });

  it('converts to JST across the date boundary', () => {
    expect(formatJaYmd('2026-02-10T15:00:00Z')).toBe('2026/02/11');
    expect(formatJaYmd('2026-02-10T14:59:59Z')).toBe('2026/02/10');
  });

  it('handles the Heisei -> Reiwa era change', () => {
    expect(formatJaEraYmd('2019-04-30T12:00:00+09:00')).toBe('平成31年04月30日');
    expect(formatJaEraYmd('2019-05-01T12:00:00+09:00')).toBe('令和01年05月01日');
  });

  it.each([
    formatJaYmd,
    formatJaYmdKanji,
    formatJaKanjiMdHms,
    formatJaKanjiYmdHms,
    formatJstDateTime,
    formatJaEraYmd,
    formatJaEraShortYmd,
    formatJaEraYmdHm,
  ])('%o returns an empty string for null', (fn) => {
    expect(fn(null)).toBe('');
  });
});

describe('ISO-style formatters (local time)', () => {
  it('formatIsoDate', () => {
    expect(formatIsoDate(SAMPLE)).toBe('2026-02-10');
  });

  it('formatIsoDateTime', () => {
    expect(formatIsoDateTime(SAMPLE)).toBe('2026-02-10 03:04:05');
  });

  it('formatIsoUtc', () => {
    expect(formatIsoUtc('2026-02-10 12:04:05.006+0900')).toBe(SAMPLE);
  });

  it.each([formatIsoDate, formatIsoDateTime, formatIsoUtc])(
    '%o returns an empty string for invalid input',
    (fn) => {
      expect(fn('invalid')).toBe('');
    },
  );
});

describe('international formatters (local time)', () => {
  it.each([
    ['formatUsDate', formatUsDate, '02/10/2026'],
    ['formatUsDateTime24', formatUsDateTime24, '02/10/2026, 03:04'],
    ['formatUsDateTime12', formatUsDateTime12, '02/10/2026, 03:04 AM'],
    ['formatUkDate', formatUkDate, '10/02/2026'],
    ['formatUkDateTime', formatUkDateTime, '10/02/2026, 03:04'],
    ['formatEnLongDate', formatEnLongDate, 'Feb 10, 2026'],
    ['formatEnLongDateTime', formatEnLongDateTime, 'Feb 10, 2026, 03:04'],
  ])('%s', (_name, fn, expected) => {
    expect(normalizeSpaces(fn(SAMPLE))).toBe(expected);
  });

  it('formatUsDateTime12 renders PM hours', () => {
    expect(normalizeSpaces(formatUsDateTime12('2026-02-10T15:30:00Z'))).toBe(
      '02/10/2026, 03:30 PM',
    );
  });
});

describe('formatByPattern', () => {
  const expected: Record<SupportedDateFormat, string> = {
    'YYYY/MM/DD': '2026/02/10',
    'YYYY-MM-DD': '2026-02-10',
    'YYYY年MM月DD日': '2026年02月10日',
    'YYYY年M月D日': '2026年2月10日',
    'YYYY年M月D日(曜)': '2026年2月10日火曜',
    'M/D': '2/10',
    'M/D(曜)': '2/10火曜',
    'YYYY/MM/DD HH:mm': '2026/02/10 03:04',
    'YYYY/MM/DD HH:mm:ss': '2026/02/10 03:04:05',
    'MM/DD HH:mm:ss': '02/10 03:04:05',
    'HH:mm': '03:04',
    'HH:mm:ss': '03:04:05',
    'YYYY-MM-DD HH:mm:ss': '2026-02-10 03:04:05',
    'MM/DD/YYYY': '02/10/2026',
    'DD/MM/YYYY': '10/02/2026',
  };

  it('has an expectation for every supported format', () => {
    expect(Object.keys(expected).sort()).toEqual([...SUPPORTED_DATE_FORMATS].sort());
  });

  it.each(SUPPORTED_DATE_FORMATS.map((p) => [p, expected[p]] as const))(
    '%s -> %s',
    (pattern, out) => {
      expect(formatByPattern(SAMPLE, pattern)).toBe(out);
    },
  );

  it('honours an explicit English weekday locale', () => {
    expect(formatByPattern(SAMPLE, 'M/D(曜)', { weekdayLocale: 'en' })).toBe('2/10Tue');
  });

  it('pads single-digit months and days only for MM/DD tokens', () => {
    expect(formatByPattern('2026-03-04T00:00:00Z', 'YYYY/MM/DD')).toBe('2026/03/04');
    expect(formatByPattern('2026-03-04T00:00:00Z', 'M/D')).toBe('3/4');
  });

  it('returns an empty string for invalid input', () => {
    expect(formatByPattern(null, 'YYYY/MM/DD')).toBe('');
    expect(formatByPattern('invalid', 'HH:mm')).toBe('');
  });
});
