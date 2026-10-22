/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

import { describe, expect, it } from 'vitest';

import {
  SUPPORTED_DATE_FORMATS,
  type SupportedDateFormat,
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
} from '@/lib/datetime';

// 2024-03-05 16:04:05.123 UTC is 2024-03-06 01:04:05.123 JST (crosses the
// date boundary), and it is a Tuesday in UTC (the pinned host timezone).
const INSTANT = '2024-03-05T16:04:05.123Z';
// 00:05 UTC, used to check how 24-hour formatters print midnight.
const MIDNIGHT = '2024-03-05T00:05:09Z';

const EMPTY_INPUTS = [null, undefined, '', '   ', 'not a date'] as const;

describe('test environment', () => {
  it('runs with the host timezone pinned to UTC', () => {
    expect(new Date(INSTANT).getTimezoneOffset()).toBe(0);
    expect(Intl.DateTimeFormat().resolvedOptions().timeZone).toBe('UTC');
  });
});

describe('normalizeIso', () => {
  it('returns an empty string for null, undefined and blank input', () => {
    expect(normalizeIso(null)).toBe('');
    expect(normalizeIso(undefined)).toBe('');
    expect(normalizeIso('')).toBe('');
    expect(normalizeIso('   ')).toBe('');
  });

  it('trims surrounding whitespace', () => {
    expect(normalizeIso('  2024-03-05T16:04:05Z \n')).toBe('2024-03-05T16:04:05Z');
  });

  it('replaces the date/time separator space with "T"', () => {
    expect(normalizeIso('2024-03-05 16:04:05')).toBe('2024-03-05T16:04:05');
  });

  it('inserts a colon into compact offsets', () => {
    expect(normalizeIso('2024-03-06T01:04:05+0900')).toBe('2024-03-06T01:04:05+09:00');
    expect(normalizeIso('2024-03-05T11:04:05-0500')).toBe('2024-03-05T11:04:05-05:00');
  });

  it('leaves offsets that already have a colon untouched', () => {
    expect(normalizeIso('2024-03-06T01:04:05+09:00')).toBe('2024-03-06T01:04:05+09:00');
  });

  it('truncates fractional seconds to milliseconds', () => {
    expect(normalizeIso('2024-03-05T16:04:05.123456Z')).toBe('2024-03-05T16:04:05.123Z');
    expect(normalizeIso('2024-03-05T16:04:05.1239Z')).toBe('2024-03-05T16:04:05.123Z');
    expect(normalizeIso('2024-03-05T16:04:05.12Z')).toBe('2024-03-05T16:04:05.12Z');
  });

  it('applies all normalizations together (PostgreSQL-style timestamp)', () => {
    expect(normalizeIso('2024-03-06 01:04:05.123456+0900')).toBe(
      '2024-03-06T01:04:05.123+09:00',
    );
  });

  it('leaves an already-normalized ISO string unchanged', () => {
    expect(normalizeIso(INSTANT)).toBe(INSTANT);
  });
});

describe('toDate', () => {
  it('returns the same Date instance for a valid Date', () => {
    const d = new Date(INSTANT);
    const result = toDate(d);
    expect(result).toBe(d);
    expect(result?.getTime()).toBe(Date.parse(INSTANT));
  });

  it('returns null for an invalid Date', () => {
    expect(toDate(new Date('nope'))).toBeNull();
  });

  it.each(EMPTY_INPUTS)('returns null for %j', (input) => {
    expect(toDate(input)).toBeNull();
  });

  it('parses ISO strings', () => {
    expect(toDate(INSTANT)?.toISOString()).toBe(INSTANT);
  });

  it('parses non-standard strings after normalization', () => {
    expect(toDate('2024-03-06 01:04:05.123456+0900')?.toISOString()).toBe(INSTANT);
  });
});

describe('formatDateTime', () => {
  it('formats with the given locale and options', () => {
    expect(
      formatDateTime(INSTANT, 'en-US', { weekday: 'long', timeZone: 'Asia/Tokyo' }),
    ).toBe('Wednesday');
  });

  it.each(EMPTY_INPUTS)('returns "" for %j', (input) => {
    expect(formatDateTime(input, 'en-US', {})).toBe('');
  });
});

describe('Japanese (JST) formatters', () => {
  const cases: [string, typeof formatJaYmd, string][] = [
    ['formatJaYmd', formatJaYmd, '2024/03/06'],
    ['formatJaYmdKanji', formatJaYmdKanji, '2024年03月06日'],
    ['formatJaYmdHm', formatJaYmdHm, '2024/03/06 01:04'],
    ['formatJaYmdHms', formatJaYmdHms, '2024/03/06 01:04:05'],
    ['formatJaKanjiMdHms', formatJaKanjiMdHms, '03月06日 01時04分05秒'],
    ['formatJaKanjiYmdHms', formatJaKanjiYmdHms, '2024年03月06日 01時04分05秒'],
    ['formatJstDateTime', formatJstDateTime, '2024年03月06日 01時04分05.123秒'],
    ['formatJaEraYmd', formatJaEraYmd, '令和06年03月06日'],
    ['formatJaEraYmdHm', formatJaEraYmdHm, '令和06年03月06日 01時04分'],
  ];

  describe.each(cases)('%s', (_name, fn, expected) => {
    it('converts a UTC instant to JST', () => {
      expect(fn(INSTANT)).toBe(expected);
    });

    it('accepts a Date object', () => {
      expect(fn(new Date(INSTANT))).toBe(expected);
    });

    it('accepts an equivalent +0900 timestamp', () => {
      expect(fn('2024-03-06 01:04:05.123+0900')).toBe(expected);
    });

    it.each(EMPTY_INPUTS)('returns "" for %j', (input) => {
      expect(fn(input)).toBe('');
    });
  });

  it('formatJaYmdHms prints JST midnight as 00, not 24', () => {
    expect(formatJaYmdHms('2024-03-05T15:05:09Z')).toBe('2024/03/06 00:05:09');
  });

  it('formatJstDateTime zero-pads milliseconds', () => {
    expect(formatJstDateTime(MIDNIGHT)).toBe('2024年03月05日 09時05分09.000秒');
  });

  it('formatJaEraYmd switches era at the Heisei/Reiwa boundary in JST', () => {
    expect(formatJaEraYmd('2019-04-30T23:59:59+09:00')).toBe('平成31年04月30日');
    expect(formatJaEraYmd('2019-04-30T15:00:00Z')).toBe('令和01年05月01日');
  });

  describe('formatJaEraShortYmd', () => {
    it('returns "" for invalid input', () => {
      expect(formatJaEraShortYmd(null)).toBe('');
      expect(formatJaEraShortYmd('not a date')).toBe('');
    });

    it('uses the JST date with a zero-padded era year', () => {
      expect(formatJaEraShortYmd(INSTANT)).toMatch(/06\/03\/06$/);
    });

    // BUG: the docstring promises "R06/02/10"-style output, but ICU's era:'short'
    // for ja-JP-u-ca-japanese is still "令和", so the actual output is "令和06/03/06".
    it.fails('uses the "R" era abbreviation documented in its docstring', () => {
      expect(formatJaEraShortYmd(INSTANT)).toBe('R06/03/06');
    });
  });
});

describe('ISO-style formatters', () => {
  it('formatIsoDate uses the host-local (UTC) date', () => {
    expect(formatIsoDate(INSTANT)).toBe('2024-03-05');
    expect(formatIsoDate('2024-03-06T01:04:05+09:00')).toBe('2024-03-05');
  });

  it('formatIsoDateTime uses host-local (UTC) 24-hour time', () => {
    expect(formatIsoDateTime(INSTANT)).toBe('2024-03-05 16:04:05');
    expect(formatIsoDateTime(MIDNIGHT)).toBe('2024-03-05 00:05:09');
  });

  it('formatIsoUtc returns toISOString()', () => {
    expect(formatIsoUtc(INSTANT)).toBe(INSTANT);
    expect(formatIsoUtc('2024-03-06 01:04:05.123456+0900')).toBe(INSTANT);
    expect(formatIsoUtc(MIDNIGHT)).toBe('2024-03-05T00:05:09.000Z');
  });

  it.each(EMPTY_INPUTS)('return "" for %j', (input) => {
    expect(formatIsoDate(input)).toBe('');
    expect(formatIsoDateTime(input)).toBe('');
    expect(formatIsoUtc(input)).toBe('');
  });
});

describe('US/UK/English formatters (host-local time)', () => {
  it('formatUsDate', () => {
    expect(formatUsDate(INSTANT)).toBe('03/05/2024');
  });

  it('formatUsDateTime24', () => {
    expect(formatUsDateTime24(INSTANT)).toBe('03/05/2024, 16:04');
  });

  it('formatUsDateTime12', () => {
    expect(formatUsDateTime12(INSTANT)).toBe('03/05/2024, 04:04 PM');
    expect(formatUsDateTime12(MIDNIGHT)).toBe('03/05/2024, 12:05 AM');
  });

  it('formatUkDate', () => {
    expect(formatUkDate(INSTANT)).toBe('05/03/2024');
  });

  it('formatUkDateTime', () => {
    expect(formatUkDateTime(INSTANT)).toBe('05/03/2024, 16:04');
    expect(formatUkDateTime(MIDNIGHT)).toBe('05/03/2024, 00:05');
  });

  it('formatEnLongDate', () => {
    expect(formatEnLongDate(INSTANT)).toBe('Mar 05, 2024');
  });

  it('formatEnLongDateTime', () => {
    expect(formatEnLongDateTime(INSTANT)).toBe('Mar 05, 2024, 16:04');
  });

  // BUG: en-US with hour12:false resolves to the h24 hour cycle, so midnight
  // prints as "24:05" instead of the documented 24-hour "00:05"
  // (hourCycle: 'h23' would fix it).
  it.fails('formatUsDateTime24 prints midnight as 00:05', () => {
    expect(formatUsDateTime24(MIDNIGHT)).toBe('03/05/2024, 00:05');
  });

  // BUG: same h24 hour cycle issue; actual output is "Mar 05, 2024, 24:05".
  it.fails('formatEnLongDateTime prints midnight as 00:05', () => {
    expect(formatEnLongDateTime(MIDNIGHT)).toBe('Mar 05, 2024, 00:05');
  });

  it.each(EMPTY_INPUTS)('return "" for %j', (input) => {
    for (const fn of [
      formatUsDate,
      formatUsDateTime24,
      formatUsDateTime12,
      formatUkDate,
      formatUkDateTime,
      formatEnLongDate,
      formatEnLongDateTime,
    ]) {
      expect(fn(input)).toBe('');
    }
  });
});

describe('formatByPattern', () => {
  // Expected output for INSTANT in host-local (UTC) time: Tue 2024-03-05 16:04:05.
  // Weekday patterns are expected to keep the parentheses, e.g. "(火)" / "(Tue)".
  const expectedJa: Record<SupportedDateFormat, string> = {
    'YYYY/MM/DD': '2024/03/05',
    'YYYY-MM-DD': '2024-03-05',
    'YYYY年MM月DD日': '2024年03月05日',
    'YYYY年M月D日': '2024年3月5日',
    'YYYY年M月D日(曜)': '2024年3月5日(火)',
    'M/D': '3/5',
    'M/D(曜)': '3/5(火)',
    'YYYY/MM/DD HH:mm': '2024/03/05 16:04',
    'YYYY/MM/DD HH:mm:ss': '2024/03/05 16:04:05',
    'MM/DD HH:mm:ss': '03/05 16:04:05',
    'HH:mm': '16:04',
    'HH:mm:ss': '16:04:05',
    'YYYY-MM-DD HH:mm:ss': '2024-03-05 16:04:05',
    'MM/DD/YYYY': '03/05/2024',
    'DD/MM/YYYY': '05/03/2024',
  };
  const expectedEn = (pattern: SupportedDateFormat) =>
    expectedJa[pattern].replace('(火)', '(Tue)');

  const isWeekdayPattern = (pattern: string) => pattern.includes('(曜)');

  it('has an expectation for every supported pattern', () => {
    expect(Object.keys(expectedJa).sort()).toEqual([...SUPPORTED_DATE_FORMATS].sort());
  });

  describe.each(SUPPORTED_DATE_FORMATS.filter((p) => !isWeekdayPattern(p)))(
    '%s',
    (pattern) => {
      it('formats with the default weekday locale', () => {
        expect(formatByPattern(INSTANT, pattern)).toBe(expectedJa[pattern]);
      });

      it.each(['ja', 'en'] as const)('formats with weekdayLocale %s', (weekdayLocale) => {
        expect(formatByPattern(INSTANT, pattern, { weekdayLocale })).toBe(
          expectedJa[pattern],
        );
      });

      it.each(EMPTY_INPUTS)('returns "" for %j', (input) => {
        expect(formatByPattern(input, pattern)).toBe('');
      });
    },
  );

  describe.each(SUPPORTED_DATE_FORMATS.filter(isWeekdayPattern))('%s', (pattern) => {
    it('substitutes the correct weekday name', () => {
      expect(formatByPattern(INSTANT, pattern)).toContain('火');
      expect(formatByPattern(INSTANT, pattern, { weekdayLocale: 'ja' })).toContain('火');
      expect(formatByPattern(INSTANT, pattern, { weekdayLocale: 'en' })).toContain('Tue');
      expect(formatByPattern('2024-03-10T12:00:00Z', pattern)).toContain('日');
      expect(
        formatByPattern('2024-03-09T12:00:00Z', pattern, { weekdayLocale: 'en' }),
      ).toContain('Sat');
    });

    it.each(EMPTY_INPUTS)('returns "" for %j', (input) => {
      expect(formatByPattern(input, pattern)).toBe('');
    });

    // BUG: "(曜)" is replaced by "火曜" (ja) / "Tue" (en), dropping the
    // parentheses, e.g. "2024年3月5日火曜" instead of "2024年3月5日(火)".
    it.fails('keeps the parentheses with the default (ja) weekday locale', () => {
      expect(formatByPattern(INSTANT, pattern)).toBe(expectedJa[pattern]);
    });

    // BUG: see above; actual output for weekdayLocale 'ja' contains "火曜".
    it.fails('keeps the parentheses with weekdayLocale ja', () => {
      expect(formatByPattern(INSTANT, pattern, { weekdayLocale: 'ja' })).toBe(
        expectedJa[pattern],
      );
    });

    // BUG: see above; actual output for weekdayLocale 'en' is e.g. "3/5Tue".
    it.fails('keeps the parentheses with weekdayLocale en', () => {
      expect(formatByPattern(INSTANT, pattern, { weekdayLocale: 'en' })).toBe(
        expectedEn(pattern),
      );
    });
  });

  it('uses host-local (UTC) time, not JST', () => {
    expect(formatByPattern('2024-03-06T01:04:05+09:00', 'YYYY/MM/DD HH:mm')).toBe(
      '2024/03/05 16:04',
    );
  });

  it('accepts a Date object', () => {
    expect(formatByPattern(new Date(INSTANT), 'YYYY-MM-DD HH:mm:ss')).toBe(
      '2024-03-05 16:04:05',
    );
  });
});
