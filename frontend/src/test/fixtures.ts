import type { JobActiveResponse, StatementTaskResponse } from '@/types/job';

export function makeTask(overrides: Partial<StatementTaskResponse> = {}): StatementTaskResponse {
  return {
    type: 'robot_move',
    id: 'task-1',
    name: 'Move to A',
    next: null,
    should_show: true,
    can_recover: false,
    finished: false,
    command: [],
    ...overrides,
  };
}

export function makeJob(overrides: Partial<JobActiveResponse> = {}): JobActiveResponse {
  const task = makeTask();
  return {
    id: 'job-1',
    created_at: '2026-02-10T00:00:00Z',
    name: 'Pallet run',
    visible: true,
    task,
    variables: [],
    command: { type: 'task', id: task.id },
    error_msg: [],
    warning_msg: [],
    ...overrides,
  };
}
