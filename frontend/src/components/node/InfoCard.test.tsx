import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/render';
import InfoCard from './InfoCard';

describe('InfoCard', () => {
  it('shows the translated default title and empty message', () => {
    renderWithProviders(<InfoCard />);
    expect(screen.getByText('情報')).toBeInTheDocument();
    expect(screen.getByText('(情報はありません)')).toBeInTheDocument();
  });

  it('treats an empty array as no info', () => {
    renderWithProviders(<InfoCard info={[]} />);
    expect(screen.getByText('(情報はありません)')).toBeInTheDocument();
  });

  it('renders each info message and a custom title', () => {
    renderWithProviders(<InfoCard title="Robot status" info={['Charging', 'Idle at dock']} />);
    expect(screen.getByText('Robot status')).toBeInTheDocument();
    expect(screen.getByText('Charging')).toBeInTheDocument();
    expect(screen.getByText('Idle at dock')).toBeInTheDocument();
    expect(screen.queryByText('(情報はありません)')).not.toBeInTheDocument();
  });
});
