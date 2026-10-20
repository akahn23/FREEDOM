import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/render';
import BatteryGauge from './BatteryGauge';

function barColor() {
  const bar = document.querySelector('.MuiLinearProgress-bar') as HTMLElement;
  return getComputedStyle(bar).backgroundColor;
}

describe('BatteryGauge', () => {
  it('renders a determinate progress bar with the battery level', () => {
    renderWithProviders(<BatteryGauge level={72} />);
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '72');
  });

  it('falls back to 0 when level is falsy', () => {
    renderWithProviders(<BatteryGauge level={Number.NaN} />);
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0');
  });

  it.each([
    [10, 'red'],
    [35, 'orange'],
    [80, 'green'],
  ])('level %i uses a %s bar', (level, color) => {
    renderWithProviders(<BatteryGauge level={level} />);
    expect(barColor()).toBe(color === 'red' ? 'rgb(255, 0, 0)' : color === 'orange' ? 'rgb(255, 165, 0)' : 'rgb(0, 128, 0)');
  });
});
