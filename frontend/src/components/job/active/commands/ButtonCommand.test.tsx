import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { renderWithProviders } from '@/test/render';
import { makeJob, makeTask } from '@/test/fixtures';
import ButtonCommand from './ButtonCommand';

const { post, confirm, show } = vi.hoisted(() => ({
  post: vi.fn(),
  confirm: vi.fn(),
  show: vi.fn(),
}));

vi.mock('@/lib/axios', () => ({ default: { post } }));
vi.mock('@toolpad/core/useDialogs', () => ({ useDialogs: () => ({ confirm }) }));
vi.mock('@toolpad/core/useNotifications', () => ({ useNotifications: () => ({ show }) }));

const job = makeJob();
const task = makeTask({ id: 'task-7' });
const command = { type: 'button' as const, label: 'Resume', value: 'resume' };

function renderButton(onRefresh = vi.fn().mockResolvedValue(undefined)) {
  renderWithProviders(
    <ButtonCommand job={job} task={task} command={command} onRefresh={onRefresh} />,
  );
  return { onRefresh, button: screen.getByRole('button', { name: 'Resume' }) };
}

describe('ButtonCommand', () => {
  beforeEach(() => {
    post.mockReset();
    confirm.mockReset();
    show.mockReset();
  });

  it('asks for confirmation with translated texts', async () => {
    confirm.mockResolvedValue(false);
    const { button } = renderButton();
    fireEvent.click(button);

    await waitFor(() => expect(confirm).toHaveBeenCalledTimes(1));
    expect(confirm).toHaveBeenCalledWith('Resume を実行しますか？', {
      title: 'Pallet run',
      okText: '実行する',
      cancelText: 'キャンセル',
    });
  });

  it('does nothing when the dialog is cancelled', async () => {
    confirm.mockResolvedValue(false);
    const { button, onRefresh } = renderButton();
    fireEvent.click(button);

    await waitFor(() => expect(confirm).toHaveBeenCalled());
    expect(post).not.toHaveBeenCalled();
    expect(onRefresh).not.toHaveBeenCalled();
    expect(show).not.toHaveBeenCalled();
  });

  it('posts exec_command, refreshes and shows success when confirmed', async () => {
    confirm.mockResolvedValue(true);
    post.mockResolvedValue({ data: null });
    const { button, onRefresh } = renderButton();
    fireEvent.click(button);

    await waitFor(() => expect(show).toHaveBeenCalled());
    expect(post).toHaveBeenCalledWith('/node/job.active', {
      domain: { id: 'job-1' },
      func: 'exec_command',
      kwargs: { command: 'resume', id: 'task-7' },
    });
    expect(onRefresh).toHaveBeenCalledTimes(1);
    expect(show).toHaveBeenCalledWith('Pallet run ジョブ Resume を実行しました', {
      severity: 'success',
      autoHideDuration: 3000,
    });
  });

  it('shows an error notification when the request fails', async () => {
    confirm.mockResolvedValue(true);
    post.mockRejectedValue(new Error('500'));
    const { button, onRefresh } = renderButton();
    fireEvent.click(button);

    await waitFor(() => expect(show).toHaveBeenCalled());
    expect(onRefresh).not.toHaveBeenCalled();
    expect(show).toHaveBeenCalledWith('Pallet run ジョブ Resume の実行に失敗しました', {
      severity: 'error',
      autoHideDuration: 3000,
    });
  });
});
