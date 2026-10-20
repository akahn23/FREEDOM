/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

import { ThemeProvider, createTheme, useTheme } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { clampMapStatus, getMapStatusColor } from './statusColors';

const theme = createTheme();

describe('clampMapStatus', () => {
  it.each([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])('keeps in-range integer %i', (n) => {
    expect(clampMapStatus(n)).toBe(n);
  });

  it('defaults undefined to 0', () => {
    expect(clampMapStatus()).toBe(0);
    expect(clampMapStatus(undefined)).toBe(0);
  });

  it.each([NaN, Infinity, -Infinity])('maps non-finite %s to 0', (n) => {
    expect(clampMapStatus(n)).toBe(0);
  });

  it.each([
    [3.9, 3],
    [4.1, 4],
    [-0.5, 0],
    [9.99, 9],
  ])('truncates fractional %s to %i', (input, expected) => {
    expect(clampMapStatus(input)).toBe(expected);
  });

  it.each([
    [-1, 0],
    [-100, 0],
    [10, 9],
    [1000, 9],
  ])('clamps out-of-range %i to %i', (input, expected) => {
    expect(clampMapStatus(input)).toBe(expected);
  });

  it('does not return -0 for small negative fractions', () => {
    expect(Object.is(clampMapStatus(-0.5), 0)).toBe(true);
  });
});

describe('getMapStatusColor', () => {
  it.each([
    [0, theme.palette.grey[400]],
    [1, theme.palette.info.main],
    [2, theme.palette.secondary.main],
    [3, theme.palette.success.main],
    [4, theme.palette.warning.main],
    [5, theme.palette.error.main],
  ])('maps status %i to its palette colour', (status, expected) => {
    expect(getMapStatusColor(theme, status)).toBe(expected);
  });

  it.each([6, 7, 8, 9])('falls back to grey[500] for reserved status %i', (status) => {
    expect(getMapStatusColor(theme, status)).toBe(theme.palette.grey[500]);
  });

  it('treats missing / invalid status as DISCONNECT (0)', () => {
    expect(getMapStatusColor(theme)).toBe(theme.palette.grey[400]);
    expect(getMapStatusColor(theme, NaN)).toBe(theme.palette.grey[400]);
    expect(getMapStatusColor(theme, -3)).toBe(theme.palette.grey[400]);
  });

  it('clamps before mapping (100 → 9 → fallback, 5.7 → ERROR)', () => {
    expect(getMapStatusColor(theme, 100)).toBe(theme.palette.grey[500]);
    expect(getMapStatusColor(theme, 5.7)).toBe(theme.palette.error.main);
  });

  it('follows a custom theme palette', () => {
    const custom = createTheme({ palette: { error: { main: '#123456' } } });
    expect(getMapStatusColor(custom, 5)).toBe('#123456');
  });

  it('can be applied from a component using the MUI theme', () => {
    function StatusDot({ status }: { status: number }) {
      const t = useTheme();
      return <span data-testid="dot" style={{ color: getMapStatusColor(t, status) }} />;
    }
    const custom = createTheme({ palette: { success: { main: '#00ff00' } } });
    render(
      <ThemeProvider theme={custom}>
        <StatusDot status={3} />
      </ThemeProvider>,
    );
    expect(screen.getByTestId('dot')).toHaveStyle({ color: '#00ff00' });
  });
});
