import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/render';
import DetailCard from './DetailCard';

describe('DetailCard', () => {
  it.each([undefined, null, [], '   '])('shows the empty message for %j', (detail) => {
    renderWithProviders(<DetailCard detail={detail} />);
    expect(screen.getByText('詳細')).toBeInTheDocument();
    expect(screen.getByText('(詳細情報はありません)')).toBeInTheDocument();
  });

  it('renders array entries as strings', () => {
    renderWithProviders(<DetailCard detail={['first', 42]} />);
    expect(screen.getByText('first')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
  });

  it('renders a string inside a <pre>', () => {
    renderWithProviders(<DetailCard detail={'line 1\nline 2'} />);
    const pre = document.querySelector('pre');
    expect(pre).toHaveTextContent('line 1 line 2');
  });

  it('pretty-prints objects as JSON', () => {
    renderWithProviders(<DetailCard title="Raw" detail={{ battery: 80, state: 'idle' }} />);
    expect(screen.getByText('Raw')).toBeInTheDocument();
    expect(document.querySelector('pre')?.textContent).toBe(
      JSON.stringify({ battery: 80, state: 'idle' }, null, 2),
    );
  });
});
