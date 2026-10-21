/** SPDX-License-Identifier: Apache-2.0 */
// @vitest-environment node

import { describe, expect, it } from 'vitest';
import {
  SUPPORTED_DATE_FORMATS,
  type DateInput,
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

// 2026-02-10 03:04:05.007 UTC == 2026-02-10 12:04:05.007 JST (a Tuesday).
const SAMPLE = '2026-02-10T03:04:05.007Z';
// Exactly midnight in JST.
const JST_MIDNIGHT = '2026-02-09T15:00:00Z';
// New Year in JST while it is still 2025 in UTC.
const JST_NEW_YEAR = '2025-12-31T15:00:00Z';

const INVALID_INPUTS: Array<[string, DateInput]> = [
  ['null', null],
  ['undefined', undefined],
  ['empty string', ''],
  ['whitespace', '   '],
  ['garbage string', 'not a date'],
  ['invalid Date', new Date(NaN)],
];

const FORMATTERS: Array<[string, typeof formatJaYmd]> = [
  ['formatJaYmd', formatJaYmd],
  ['formatJaYmdKanji', formatJaYmdKanji],
  ['formatJaYmdHm', formatJaYmdHm],
  ['formatJaYmdHms', formatJaYmdHms],
  ['formatJaKanjiMdHms', formatJaKanjiMdHms],
  ['formatJaKanjiYmdHms', formatJaKanjiYmdHms],
  ['formatJstDateTime', formatJstDateTime],
  ['formatJaEraYmd', formatJaEraYmd],
  ['formatJaEraShortYmd', formatJaEraShortYmd],
  ['formatJaEraYmdHm', formatJaEraYmdHm],
  ['formatIsoDate', formatIsoDate],
  ['formatIsoDateTime', formatIsoDateTime],
  ['formatIsoUtc', formatIsoUtc],
  ['formatUsDate', formatUsDate],
  ['formatUsDateTime24', formatUsDateTime24],
  ['formatUsDateTime12', formatUsDateTime12],
  ['formatUkDate', formatUkDate],
  ['formatUkDateTime', formatUkDateTime],
  ['formatEnLongDate', formatEnLongDate],
  ['formatEnLongDateTime', formatEnLongDateTime],
  ['formatByPattern', (v) => formatByPattern(v, 'YYYY-MM-DD')],
  ['formatDateTime', (v) => formatDateTime(v, 'en-US', { year: 'numeric' })],
];

describe('test environment', () => {
  it('runs in UTC so local-time formatters are deterministic', () => {
    expect(new Date(SAMPLE).getTimezoneOffset()).toBe(0);
    expect(Intl.DateTimeFormat().resolvedOptions().timeZone).toBe('UTC');
  });
});

describe('normalizeIso', () => {
  it.each([
    [null, ''],
    [undefined, ''],
    ['', ''],
    ['   ', ''],
  ])('returns an empty string for %j', (input, expected) => {
    expect(normalizeIso(input)).toBe(expected);
  });

  it('leaves an already normalized ISO string untouched', () => {
    expect(normalizeIso('2026-02-10T12:34:56.123Z')).toBe('2026-02-10T12:34:56.123Z');
    expect(normalizeIso('2026-02-10')).toBe('2026-02-10');
  });

  it('trims and replaces the date/time separator space with "T"', () => {
    expect(normalizeIso('  2026-02-10 12:34:56  ')).toBe('2026-02-10T12:34:56');
  });

  it('only replaces the first space', () => {
    expect(normalizeIso('2026-02-10 12:34:56 Z')).toBe('2026-02-10T12:34:56 Z');
  });

  it.each([
    ['2026-02-10T12:34:56+0900', '2026-02-10T12:34:56+09:00'],
    ['2026-02-10T12:34:56-0530', '2026-02-10T12:34:56-05:30'],
    ['2026-02-10T12:34:56+09:00', '2026-02-10T12:34:56+09:00'],
  ])('inserts a colon into a compact offset: %s', (input, expected) => {
    expect(normalizeIso(input)).toBe(expected);
  });

  it('truncates fractional seconds to milliseconds', () => {
    expect(normalizeIso('2026-02-10T12:34:56.123456Z')).toBe('2026-02-10T12:34:56.123Z');
    expect(normalizeIso('2026-02-10T12:34:56.1Z')).toBe('2026-02-10T12:34:56.1Z');
  });

  it('normalizes a PostgreSQL style timestamp in one go', () => {
    expect(normalizeIso('2026-02-10 12:34:56.123456+0900')).toBe(
      '2026-02-10T12:34:56.123+09:00',
    );
  });
});

describe('toDate', () => {
  it.each(INVALID_INPUTS)('returns null for %s', (_label, input) => {
    expect(toDate(input)).toBeNull();
  });

  it('returns the same instance for a valid Date', () => {
    const d = new Date(SAMPLE);
    expect(toDate(d)).toBe(d);
  });

  it('parses ISO strings with Z and explicit offsets', () => {
    expect(toDate(SAMPLE)?.toISOString()).toBe(SAMPLE);
    expect(toDate('2026-02-10T12:04:05.007+09:00')?.toISOString()).toBe(SAMPLE);
  });

  it('parses non-standard strings after normalization', () => {
    expect(toDate('2026-02-10 12:04:05.007999+0900')?.toISOString()).toBe(SAMPLE);
  });

  it('treats a zone-less date-time as local time (UTC in tests)', () => {
    expect(toDate('2026-02-10 03:04:05')?.toISOString()).toBe('2026-02-10T03:04:05.000Z');
  });

  it('rejects out-of-range dates', () => {
    expect(toDate('2026-13-01')).toBeNull();
  });
});

describe('formatDateTime', () => {
  it('formats with the given locale and options', () => {
    expect(
      formatDateTime(SAMPLE, 'en-US', { year: 'numeric', month: 'long', timeZone: 'UTC' }),
    ).toBe('February 2026');
    expect(
      formatDateTime(SAMPLE, 'de-DE', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        timeZone: 'UTC',
      }),
    ).toBe('10.02.2026');
  });

  it('accepts Date objects', () => {
    expect(formatDateTime(new Date(SAMPLE), 'en-GB', { weekday: 'long', timeZone: 'UTC' })).toBe(
      'Tuesday',
    );
  });
});

describe.each(FORMATTERS)('%s with invalid input', (_name, fn) => {
  it.each(INVALID_INPUTS)('returns an empty string for %s', (_label, input) => {
    expect(fn(input)).toBe('');
  });
});

describe('Japanese Gregorian formatters (fixed to JST)', () => {
  it('formatJaYmd', () => {
    expect(formatJaYmd(SAMPLE)).toBe('2026/02/10');
    expect(formatJaYmd(new Date(SAMPLE))).toBe('2026/02/10');
  });

  it('formatJaYmdKanji', () => {
    expect(formatJaYmdKanji(SAMPLE)).toBe('2026年02月10日');
  });

  it('formatJaYmdHm', () => {
    expect(formatJaYmdHm(SAMPLE)).toBe('2026/02/10 12:04');
  });

  it('formatJaYmdHms', () => {
    expect(formatJaYmdHms(SAMPLE)).toBe('2026/02/10 12:04:05');
  });

  it('formatJaKanjiMdHms', () => {
    expect(formatJaKanjiMdHms(SAMPLE)).toBe('02月10日 12時04分05秒');
  });

  it('formatJaKanjiYmdHms', () => {
    expect(formatJaKanjiYmdHms(SAMPLE)).toBe('2026年02月10日 12時04分05秒');
  });

  it('formatJstDateTime includes zero-padded milliseconds', () => {
    expect(formatJstDateTime(SAMPLE)).toBe('2026年02月10日 12時04分05.007秒');
    expect(formatJstDateTime('2026-02-10T03:04:05Z')).toBe('2026年02月10日 12時04分05.000秒');
    expect(formatJstDateTime('2026-02-10T03:04:05.999999Z')).toBe(
      '2026年02月10日 12時04分05.999秒',
    );
  });

  it('converts to JST across the midnight boundary', () => {
    expect(formatJaYmdHms('2026-02-09T14:59:59Z')).toBe('2026/02/09 23:59:59');
    expect(formatJaYmdHms(JST_MIDNIGHT)).toBe('2026/02/10 00:00:00');
    expect(formatJaKanjiMdHms(JST_MIDNIGHT)).toBe('02月10日 00時00分00秒');
    expect(formatJaYmdHm(JST_MIDNIGHT)).toBe('2026/02/10 00:00');
  });

  it('rolls over month and year in JST', () => {
    expect(formatJaYmd('2026-01-31T15:00:00Z')).toBe('2026/02/01');
    expect(formatJaYmd(JST_NEW_YEAR)).toBe('2026/01/01');
    expect(formatJaKanjiYmdHms(JST_NEW_YEAR)).toBe('2026年01月01日 00時00分00秒');
    expect(formatJstDateTime(JST_NEW_YEAR)).toBe('2026年01月01日 00時00分00.000秒');
  });

  it('handles leap days', () => {
    expect(formatJaYmdKanji('2024-02-29T00:00:00Z')).toBe('2024年02月29日');
  });

  it('interprets explicit offsets before converting to JST', () => {
    expect(formatJaYmdHms('2026-02-10 12:04:05+0900')).toBe('2026/02/10 12:04:05');
    expect(formatJaYmdHms('2026-02-09T22:04:05-05:00')).toBe('2026/02/10 12:04:05');
  });
});

describe('Japanese era (wareki) formatters', () => {
  it('formatJaEraYmd pads the era year to two digits', () => {
    expect(formatJaEraYmd(SAMPLE)).toBe('令和08年02月10日');
    expect(formatJaEraYmd('2024-02-10T00:00:00Z')).toBe('令和06年02月10日');
  });

  it('switches from Heisei to Reiwa at 2019-05-01 00:00 JST', () => {
    expect(formatJaEraYmd('2019-04-30T14:59:59Z')).toBe('平成31年04月30日');
    expect(formatJaEraYmd('2019-04-30T15:00:00Z')).toBe('令和01年05月01日');
  });

  it('handles the Showa to Heisei transition (1989-01-08)', () => {
    expect(formatJaEraYmd('1989-01-07T00:00:00Z')).toBe('昭和64年01月07日');
    expect(formatJaEraYmd('1989-01-08T00:00:00Z')).toBe('平成01年01月08日');
  });

  it('formatJaEraShortYmd currently outputs the full era name from ICU', () => {
    expect(formatJaEraShortYmd('2024-02-10T00:00:00Z')).toBe('令和06/02/10');
    expect(formatJaEraShortYmd('2019-04-30T14:59:59Z')).toBe('平成31/04/30');
  });

  // Known issue: the doc comment promises "R06/02/10", but ICU's short era
  // name for ja-JP is "令和", so the abbreviated Latin letter is never produced.
  it.fails('formatJaEraShortYmd matches its documented "R06/02/10" output', () => {
    expect(formatJaEraShortYmd('2024-02-10T00:00:00Z')).toBe('R06/02/10');
  });

  it('formatJaEraYmdHm', () => {
    expect(formatJaEraYmdHm(SAMPLE)).toBe('令和08年02月10日 12時04分');
    expect(formatJaEraYmdHm(JST_MIDNIGHT)).toBe('令和08年02月10日 00時00分');
  });
});

describe('ISO-like formatters (local time zone)', () => {
  it('formatIsoDate', () => {
    expect(formatIsoDate(SAMPLE)).toBe('2026-02-10');
    expect(formatIsoDate('2026-01-05T23:59:59Z')).toBe('2026-01-05');
    expect(formatIsoDate('2026-02-10T08:00:00+09:00')).toBe('2026-02-09');
  });

  it('formatIsoDateTime', () => {
    expect(formatIsoDateTime(SAMPLE)).toBe('2026-02-10 03:04:05');
    expect(formatIsoDateTime('2025-12-31T23:59:59Z')).toBe('2025-12-31 23:59:59');
    expect(formatIsoDateTime('2026-01-01T00:00:00Z')).toBe('2026-01-01 00:00:00');
  });

  it('formatIsoUtc returns the full UTC ISO string', () => {
    expect(formatIsoUtc(SAMPLE)).toBe(SAMPLE);
    expect(formatIsoUtc('2026-02-10 12:04:05+0900')).toBe('2026-02-10T03:04:05.000Z');
    expect(formatIsoUtc(new Date(Date.UTC(2026, 0, 1)))).toBe('2026-01-01T00:00:00.000Z');
  });
});

describe('international formatters (local time zone)', () => {
  it('formatUsDate', () => {
    expect(formatUsDate(SAMPLE)).toBe('02/10/2026');
  });

  it('formatUsDateTime24', () => {
    expect(formatUsDateTime24('2026-02-10T13:45:00Z')).toBe('02/10/2026, 13:45');
  });

  it('formatUsDateTime12', () => {
    expect(formatUsDateTime12('2026-02-10T13:45:00Z')).toMatch(/^02\/10\/2026, 01:45\sPM$/u);
    expect(formatUsDateTime12('2026-02-10T00:05:00Z')).toMatch(/^02\/10\/2026, 12:05\sAM$/u);
  });

  it('formatUkDate', () => {
    expect(formatUkDate(SAMPLE)).toBe('10/02/2026');
  });

  it('formatUkDateTime uses 00 for midnight', () => {
    expect(formatUkDateTime('2026-02-10T13:45:00Z')).toBe('10/02/2026, 13:45');
    expect(formatUkDateTime('2026-02-10T00:05:00Z')).toBe('10/02/2026, 00:05');
  });

  it('formatEnLongDate', () => {
    expect(formatEnLongDate(SAMPLE)).toBe('Feb 10, 2026');
    expect(formatEnLongDate('2026-01-01T00:00:00Z')).toBe('Jan 01, 2026');
  });

  it('formatEnLongDateTime', () => {
    expect(formatEnLongDateTime('2026-02-10T13:45:00Z')).toBe('Feb 10, 2026, 13:45');
  });

  it('en-US 24-hour formatters currently render midnight as hour 24', () => {
    expect(formatUsDateTime24('2026-02-10T00:05:00Z')).toBe('02/10/2026, 24:05');
    expect(formatEnLongDateTime('2026-02-10T00:05:00Z')).toBe('Feb 10, 2026, 24:05');
  });

  // Known issue: `hour12: false` with en-US resolves to the h24 hour cycle in
  // ICU, so 00:05 is printed as "24:05". `hourCycle: 'h23'` would fix it.
  it.fails('formatUsDateTime24 renders midnight as 00:xx', () => {
    expect(formatUsDateTime24('2026-02-10T00:05:00Z')).toBe('02/10/2026, 00:05');
  });

  it.fails('formatEnLongDateTime renders midnight as 00:xx', () => {
    expect(formatEnLongDateTime('2026-02-10T00:05:00Z')).toBe('Feb 10, 2026, 00:05');
  });
});

describe('formatByPattern', () => {
  // Tuesday, single-digit month/day/hour/minute/second to tell M from MM.
  const D = '2026-02-03T04:05:06Z';

  const EXPECTED: Record<SupportedDateFormat, string> = {
    'YYYY/MM/DD': '2026/02/03',
    'YYYY-MM-DD': '2026-02-03',
    'YYYY年MM月DD日': '2026年02月03日',
    'YYYY年M月D日': '2026年2月3日',
    'YYYY年M月D日(曜)': '2026年2月3日火曜',
    'M/D': '2/3',
    'M/D(曜)': '2/3火曜',
    'YYYY/MM/DD HH:mm': '2026/02/03 04:05',
    'YYYY/MM/DD HH:mm:ss': '2026/02/03 04:05:06',
    'MM/DD HH:mm:ss': '02/03 04:05:06',
    'HH:mm': '04:05',
    'HH:mm:ss': '04:05:06',
    'YYYY-MM-DD HH:mm:ss': '2026-02-03 04:05:06',
    'MM/DD/YYYY': '02/03/2026',
    'DD/MM/YYYY': '03/02/2026',
  };

  it('has an expectation for every supported format', () => {
    expect(Object.keys(EXPECTED).sort()).toEqual([...SUPPORTED_DATE_FORMATS].sort());
  });

  it.each(SUPPORTED_DATE_FORMATS.map((p) => [p, EXPECTED[p]] as const))(
    'formats %s',
    (pattern, expected) => {
      expect(formatByPattern(D, pattern)).toBe(expected);
    },
  );

  it('uses two-digit fields for double-digit values', () => {
    expect(formatByPattern('2026-12-31T23:59:58Z', 'YYYY-MM-DD HH:mm:ss')).toBe(
      '2026-12-31 23:59:58',
    );
    expect(formatByPattern('2026-12-31T23:59:58Z', 'YYYY年M月D日')).toBe('2026年12月31日');
  });

  it('handles midnight and the year rollover', () => {
    expect(formatByPattern('2025-12-31T23:59:59Z', 'YYYY/MM/DD HH:mm:ss')).toBe(
      '2025/12/31 23:59:59',
    );
    expect(formatByPattern('2026-01-01T00:00:00Z', 'YYYY/MM/DD HH:mm:ss')).toBe(
      '2026/01/01 00:00:00',
    );
  });

  it('uses the local (UTC) time zone, not JST', () => {
    expect(formatByPattern(JST_MIDNIGHT, 'YYYY-MM-DD HH:mm:ss')).toBe('2026-02-09 15:00:00');
  });

  it.each([
    ['2026-02-08T12:00:00Z', '日'],
    ['2026-02-09T12:00:00Z', '月'],
    ['2026-02-10T12:00:00Z', '火'],
    ['2026-02-11T12:00:00Z', '水'],
    ['2026-02-12T12:00:00Z', '木'],
    ['2026-02-13T12:00:00Z', '金'],
    ['2026-02-14T12:00:00Z', '土'],
  ])('renders the Japanese weekday for %s', (input, weekday) => {
    expect(formatByPattern(input, 'M/D(曜)')).toBe(`2/${new Date(input).getUTCDate()}${weekday}曜`);
  });

  it('renders the English weekday when weekdayLocale is "en"', () => {
    expect(formatByPattern(D, 'M/D(曜)', { weekdayLocale: 'en' })).toBe('2/3Tue');
    expect(formatByPattern('2026-02-08T00:00:00Z', 'YYYY年M月D日(曜)', { weekdayLocale: 'en' })).toBe(
      '2026年2月8日Sun',
    );
  });

  it('weekdayLocale has no effect on patterns without a weekday', () => {
    expect(formatByPattern(D, 'YYYY-MM-DD', { weekdayLocale: 'ja' })).toBe('2026-02-03');
    expect(formatByPattern(D, 'YYYY年MM月DD日', { weekdayLocale: 'en' })).toBe('2026年02月03日');
  });

  it('accepts Date objects and normalizable strings', () => {
    expect(formatByPattern(new Date(D), 'HH:mm:ss')).toBe('04:05:06');
    expect(formatByPattern('2026-02-03 13:05:06+0900', 'HH:mm:ss')).toBe('04:05:06');
  });
});
