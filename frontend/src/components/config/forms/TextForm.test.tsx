import type { ReactNode } from 'react';
import { describe, expect, it } from 'vitest';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { FormProvider, useForm } from 'react-hook-form';
import { renderWithProviders } from '@/test/render';
import type { TextFormResponse } from '@/types/config';
import TextForm from './TextForm';

function Harness({ children, defaultValue = '' }: { children: ReactNode; defaultValue?: string }) {
  const methods = useForm({ defaultValues: { name: defaultValue }, mode: 'onChange' });
  return (
    <FormProvider {...methods}>
      <form onSubmit={methods.handleSubmit(() => {})}>
        {children}
        <button type="submit">submit</button>
      </form>
    </FormProvider>
  );
}

const baseForm: TextFormResponse = { type: 'text', label: 'Robot name' };

describe('TextForm', () => {
  it('renders a labelled text field with the default value', () => {
    renderWithProviders(
      <Harness defaultValue="AGV-1">
        <TextForm name="name" form={baseForm} />
      </Harness>,
    );
    expect(screen.getByLabelText(/Robot name/)).toHaveValue('AGV-1');
  });

  it('renders prefix/suffix adornments', () => {
    renderWithProviders(
      <Harness>
        <TextForm name="name" form={{ ...baseForm, prefix: 'http://', suffix: '/api' }} />
      </Harness>,
    );
    expect(screen.getByText('http://')).toBeInTheDocument();
    expect(screen.getByText('/api')).toBeInTheDocument();
  });

  it('can be disabled', () => {
    renderWithProviders(
      <Harness>
        <TextForm name="name" form={baseForm} disabled />
      </Harness>,
    );
    expect(screen.getByLabelText(/Robot name/)).toBeDisabled();
  });

  it('shows the translated required error on empty submit', async () => {
    renderWithProviders(
      <Harness>
        <TextForm name="name" form={baseForm} />
      </Harness>,
    );
    fireEvent.click(screen.getByRole('button', { name: 'submit' }));
    expect(await screen.findByText('入力が必須の項目です')).toBeInTheDocument();
    expect(screen.getByLabelText(/Robot name/)).toHaveAttribute('aria-invalid', 'true');
  });

  it('does not require a value when required is false', async () => {
    renderWithProviders(
      <Harness>
        <TextForm name="name" form={{ ...baseForm, required: false }} />
      </Harness>,
    );
    fireEvent.click(screen.getByRole('button', { name: 'submit' }));
    await waitFor(() => {
      expect(screen.getByLabelText(/Robot name/)).toHaveAttribute('aria-invalid', 'false');
    });
    expect(screen.queryByText('入力が必須の項目です')).not.toBeInTheDocument();
  });
});
