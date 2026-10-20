/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

import { describe, expect, it } from 'vitest';
import { normalizeIso, toDate } from './datetime';

describe('test environment', () => {
  it('runs in UTC', () => {
    expect(new Date(2026, 0, 1).getTimezoneOffset()).toBe(0);
  });
});

describe('normalizeIso', () => {
  it.each([null, undefined, '', '   '])('returns "" for empty input %j', (input) => {
    expect(normalizeIso(input)).toBe('');
  });

  it('trims surrounding whitespace', () => {
    expect(normalizeIso('  2026-02-10T12:34:56Z  ')).toBe('2026-02-10T12:34:56Z');
  });

  it('leaves an already-normalized ISO string unchanged', () => {
    expect(normalizeIso('2026-02-10T12:34:56.789+09:00')).toBe('2026-02-10T12:34:56.789+09:00');
  });

  it('replaces the date/time separator space with "T"', () => {
    expect(normalizeIso('2026-02-10 12:34:56')).toBe('2026-02-10T12:34:56');
  });

  it('only replaces the first space', () => {
    expect(normalizeIso('2026-02-10 12:34:56 +0900')).toBe('2026-02-10T12:34:56 +09:00');
  });

  it.each([
    ['2026-02-10T12:34:56+0900', '2026-02-10T12:34:56+09:00'],
    ['2026-02-10T12:34:56-0530', '2026-02-10T12:34:56-05:30'],
    ['2026-02-10T12:34:56+0000', '2026-02-10T12:34:56+00:00'],
  ])('inserts a colon into a compact offset: %s', (input, expected) => {
    expect(normalizeIso(input)).toBe(expected);
  });

  it('does not touch a date-only string', () => {
    expect(normalizeIso('2026-02-10')).toBe('2026-02-10');
  });

  it.each([
    ['2026-02-10T12:34:56.123456Z', '2026-02-10T12:34:56.123Z'],
    ['2026-02-10T12:34:56.123456789+09:00', '2026-02-10T12:34:56.123+09:00'],
    ['2026-02-10T12:34:56.1234', '2026-02-10T12:34:56.123'],
  ])('truncates fractional seconds to milliseconds: %s', (input, expected) => {
    expect(normalizeIso(input)).toBe(expected);
  });

  it('keeps fractions with 3 or fewer digits as-is', () => {
    expect(normalizeIso('2026-02-10T12:34:56.1Z')).toBe('2026-02-10T12:34:56.1Z');
  });

  it('normalizes a Python/PostgreSQL style timestamp end to end', () => {
    expect(normalizeIso('2026-02-10 12:34:56.123456+0900')).toBe('2026-02-10T12:34:56.123+09:00');
  });

  it('passes non-date strings through', () => {
    expect(normalizeIso('not a date')).toBe('notTa date');
  });
});

describe('toDate', () => {
  it.each([null, undefined, '', '   '])('returns null for empty input %j', (input) => {
    expect(toDate(input)).toBeNull();
  });

  it('returns null for an unparsable string', () => {
    expect(toDate('not a date')).toBeNull();
  });

  it('returns null for an invalid Date', () => {
    expect(toDate(new Date('invalid'))).toBeNull();
  });

  it('returns the same Date instance for a valid Date', () => {
    const d = new Date('2026-02-10T00:00:00Z');
    expect(toDate(d)).toBe(d);
  });

  it('parses a UTC ISO string', () => {
    expect(toDate('2026-02-10T12:34:56Z')?.toISOString()).toBe('2026-02-10T12:34:56.000Z');
  });

  it('parses a compact offset and microseconds after normalization', () => {
    expect(toDate('2026-02-10 12:34:56.123456+0900')?.toISOString()).toBe(
      '2026-02-10T03:34:56.123Z',
    );
  });

  it('parses an offset-less timestamp as local time (UTC in tests)', () => {
    expect(toDate('2026-02-10 12:34:56')?.toISOString()).toBe('2026-02-10T12:34:56.000Z');
  });

  it('parses a date-only string as UTC midnight', () => {
    expect(toDate('2026-02-10')?.toISOString()).toBe('2026-02-10T00:00:00.000Z');
  });

  it('returns null for an out-of-range date', () => {
    expect(toDate('2026-13-40T00:00:00Z')).toBeNull();
  });
});
