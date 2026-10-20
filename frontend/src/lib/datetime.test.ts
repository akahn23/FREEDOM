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
} from './datetime';

// vitest.config.ts pins process.env.TZ to UTC, so "local" helpers are deterministic.
// 2026-02-10T15:30:45.678Z is 2026-02-11 00:30:45.678 in Asia/Tokyo.
const UTC_ISO = '2026-02-10T15:30:45.678Z';

describe('normalizeIso', () => {
  it.each([null, undefined, '', '   '])('returns "" for %j', (input) => {
    expect(normalizeIso(input)).toBe('');
  });

  it('replaces the date/time space with "T"', () => {
    expect(normalizeIso('2026-02-10 12:34:56')).toBe('2026-02-10T12:34:56');
  });

  it('adds a colon to compact offsets', () => {
    expect(normalizeIso('2026-02-10T12:34:56+0900')).toBe('2026-02-10T12:34:56+09:00');
    expect(normalizeIso('2026-02-10T12:34:56-0530')).toBe('2026-02-10T12:34:56-05:30');
  });

  it('truncates fractional seconds to milliseconds', () => {
    expect(normalizeIso('2026-02-10T12:34:56.123456Z')).toBe('2026-02-10T12:34:56.123Z');
  });

  it('handles a Python-style timestamp end to end', () => {
    expect(normalizeIso(' 2026-02-10 12:34:56.123456+0900 ')).toBe(
      '2026-02-10T12:34:56.123+09:00',
    );
  });
});

describe('toDate', () => {
  it('returns the same Date instance when valid', () => {
    const d = new Date(UTC_ISO);
    expect(toDate(d)).toBe(d);
  });

  it('returns null for an invalid Date', () => {
    expect(toDate(new Date('nope'))).toBeNull();
  });

  it.each([null, undefined, '', 'not a date'])('returns null for %j', (input) => {
    expect(toDate(input)).toBeNull();
  });

  it('parses normalized ISO strings with offsets', () => {
    expect(toDate('2026-02-10 09:00:00.123456+0900')?.toISOString()).toBe(
      '2026-02-10T00:00:00.123Z',
    );
  });
});

describe('formatDateTime', () => {
  it('formats with the given locale/options', () => {
    expect(formatDateTime(UTC_ISO, 'en-US', { year: 'numeric', timeZone: 'UTC' })).toBe('2026');
  });

  it('returns "" for unparsable input', () => {
    expect(formatDateTime('garbage', 'en-US', {})).toBe('');
  });
});

describe('Japanese (Gregorian) formatters use JST regardless of local TZ', () => {
  it.each([
    ['formatJaYmd', formatJaYmd, '2026/02/11'],
    ['formatJaYmdKanji', formatJaYmdKanji, '2026年02月11日'],
    ['formatJaYmdHm', formatJaYmdHm, '2026/02/11 00:30'],
    ['formatJaYmdHms', formatJaYmdHms, '2026/02/11 00:30:45'],
    ['formatJaKanjiMdHms', formatJaKanjiMdHms, '02月11日 00時30分45秒'],
    ['formatJaKanjiYmdHms', formatJaKanjiYmdHms, '2026年02月11日 00時30分45秒'],
    ['formatJstDateTime', formatJstDateTime, '2026年02月11日 00時30分45.678秒'],
  ])('%s', (_name, fn, expected) => {
    expect(fn(UTC_ISO)).toBe(expected);
  });

  it('pads milliseconds in formatJstDateTime', () => {
    expect(formatJstDateTime('2026-02-10T15:30:45.007Z')).toBe('2026年02月11日 00時30分45.007秒');
  });
});

describe('Japanese era formatters', () => {
  const REIWA_6 = '2024-02-10T03:04:00Z';

  it('formatJaEraYmd', () => {
    expect(formatJaEraYmd(REIWA_6)).toBe('令和06年02月10日');
  });

  it('formatJaEraYmdHm', () => {
    expect(formatJaEraYmdHm(REIWA_6)).toBe('令和06年02月10日 12時04分');
  });

  it('formatJaEraShortYmd (ICU short era for ja is still "令和", not "R" as the doc comment says)', () => {
    expect(formatJaEraShortYmd(REIWA_6)).toBe('令和06/02/10');
  });

  it('switches era at the Heisei/Reiwa boundary (JST)', () => {
    expect(formatJaEraYmd('2019-04-30T14:59:59Z')).toMatch(/^平成31年04月30日$/);
    expect(formatJaEraYmd('2019-04-30T15:00:00Z')).toMatch(/^令和/);
  });
});

describe('ISO-style formatters (local time = UTC in tests)', () => {
  it('formatIsoDate', () => {
    expect(formatIsoDate(UTC_ISO)).toBe('2026-02-10');
  });

  it('formatIsoDateTime', () => {
    expect(formatIsoDateTime(UTC_ISO)).toBe('2026-02-10 15:30:45');
  });

  it('formatIsoUtc', () => {
    expect(formatIsoUtc('2026-02-11 00:30:45.678+0900')).toBe(UTC_ISO);
  });
});

describe('international formatters (local time = UTC in tests)', () => {
  it.each([
    ['formatUsDate', formatUsDate, '02/10/2026'],
    ['formatUsDateTime24', formatUsDateTime24, '02/10/2026, 15:30'],
    ['formatUsDateTime12', formatUsDateTime12, '02/10/2026, 03:30 PM'],
    ['formatUkDate', formatUkDate, '10/02/2026'],
    ['formatUkDateTime', formatUkDateTime, '10/02/2026, 15:30'],
    ['formatEnLongDate', formatEnLongDate, 'Feb 10, 2026'],
    ['formatEnLongDateTime', formatEnLongDateTime, 'Feb 10, 2026, 15:30'],
  ])('%s', (_name, fn, expected) => {
    // ICU may use U+202F (narrow no-break space) before AM/PM.
    expect(fn(UTC_ISO).replace(/\u202f/g, ' ')).toBe(expected);
  });
});

describe('all formatters return "" for empty/invalid input', () => {
  const fns = [
    formatJaYmd, formatJaYmdKanji, formatJaYmdHm, formatJaYmdHms, formatJaKanjiMdHms,
    formatJaKanjiYmdHms, formatJstDateTime, formatJaEraYmd, formatJaEraShortYmd,
    formatJaEraYmdHm, formatIsoDate, formatIsoDateTime, formatIsoUtc, formatUsDate,
    formatUsDateTime24, formatUsDateTime12, formatUkDate, formatUkDateTime,
    formatEnLongDate, formatEnLongDateTime,
  ];
  it.each(fns.map((fn) => [fn.name, fn] as const))('%s', (_name, fn) => {
    expect(fn(null)).toBe('');
    expect(fn('invalid')).toBe('');
  });
});

describe('formatByPattern', () => {
  // Tuesday 2026-02-03 04:05:06 local (UTC)
  const d = '2026-02-03T04:05:06Z';

  it.each([
    ['YYYY/MM/DD', '2026/02/03'],
    ['YYYY-MM-DD', '2026-02-03'],
    ['YYYY年MM月DD日', '2026年02月03日'],
    ['YYYY年M月D日', '2026年2月3日'],
    ['YYYY年M月D日(曜)', '2026年2月3日火曜'],
    ['M/D', '2/3'],
    ['M/D(曜)', '2/3火曜'],
    ['YYYY/MM/DD HH:mm', '2026/02/03 04:05'],
    ['YYYY/MM/DD HH:mm:ss', '2026/02/03 04:05:06'],
    ['MM/DD HH:mm:ss', '02/03 04:05:06'],
    ['HH:mm', '04:05'],
    ['HH:mm:ss', '04:05:06'],
    ['YYYY-MM-DD HH:mm:ss', '2026-02-03 04:05:06'],
    ['MM/DD/YYYY', '02/03/2026'],
    ['DD/MM/YYYY', '03/02/2026'],
  ] as const)('%s → %s', (pattern, expected) => {
    expect(formatByPattern(d, pattern)).toBe(expected);
  });

  it('covers every SUPPORTED_DATE_FORMATS entry', () => {
    for (const p of SUPPORTED_DATE_FORMATS) {
      expect(formatByPattern(d, p)).not.toBe('');
    }
  });

  it('uses English weekday names when weekdayLocale is "en"', () => {
    expect(formatByPattern(d, 'M/D(曜)', { weekdayLocale: 'en' })).toBe('2/3Tue');
  });

  it('returns "" for invalid input', () => {
    expect(formatByPattern('invalid', 'YYYY/MM/DD')).toBe('');
  });
});
