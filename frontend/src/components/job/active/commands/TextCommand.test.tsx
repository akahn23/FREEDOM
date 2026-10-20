import { describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/render';
import { makeJob, makeTask } from '@/test/fixtures';
import TextCommand from './TextCommand';

describe('TextCommand', () => {
  it('renders the command label', () => {
    renderWithProviders(
      <TextCommand
        job={makeJob()}
        task={makeTask()}
        command={{ type: 'text', label: 'Waiting for operator' }}
        onRefresh={vi.fn()}
      />,
    );
    expect(screen.getByText('Waiting for operator')).toBeInTheDocument();
  });
});
