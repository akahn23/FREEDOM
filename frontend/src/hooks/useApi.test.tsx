/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

import { act, renderHook, waitFor } from '@testing-library/react';
import { AxiosError } from 'axios';
import type { Dispatch, SetStateAction } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import useApi from './useApi';

const { request } = vi.hoisted(() => ({ request: vi.fn() }));

vi.mock('@/lib/axios', () => ({ default: { request } }));

type Actions<T> = { setResponse: Dispatch<SetStateAction<T | null>>; request: () => void };

function setup<T>(...args: Parameters<typeof useApi<T>>) {
  const hook = renderHook(() => useApi<T>(...args));
  const state = () => {
    const [response, error, loading, actions] = hook.result.current;
    return {
      response: response as T | null,
      error: error as AxiosError | null,
      loading: loading as boolean,
      actions: actions as Actions<T>,
    };
  };
  return { ...hook, state };
}

function deferred<T>(): PromiseWithResolvers<T> {
  const d = {} as PromiseWithResolvers<T>;
  d.promise = new Promise<T>((resolve, reject) => {
    d.resolve = resolve;
    d.reject = reject;
  });
  return d;
}

beforeEach(() => {
  request.mockReset();
});

describe('useApi', () => {
  it('starts idle with the initial state and does not request on mount', () => {
    const { state } = setup<string[]>('get', '/robots', ['seed']);

    expect(state().response).toEqual(['seed']);
    expect(state().error).toBeNull();
    expect(state().loading).toBe(false);
    expect(typeof state().actions.request).toBe('function');
    expect(request).not.toHaveBeenCalled();
  });

  it('defaults the initial response to null', () => {
    const { state } = setup('get', '/robots');
    expect(state().response).toBeNull();
  });

  it('sets loading while in flight, then stores response.data', async () => {
    const pending = deferred<{ data: { id: number } }>();
    request.mockReturnValueOnce(pending.promise);
    const { state } = setup<{ id: number }>('get', '/robots/1');

    act(() => state().actions.request());
    expect(state().loading).toBe(true);

    await act(async () => pending.resolve({ data: { id: 1 } }));

    expect(state().response).toEqual({ id: 1 });
    expect(state().error).toBeNull();
    expect(state().loading).toBe(false);
  });

  it('stores the AxiosError and keeps the previous response on failure', async () => {
    const err = new AxiosError('Request failed with status code 500', 'ERR_BAD_RESPONSE');
    request.mockRejectedValueOnce(err);
    const { state } = setup<string>('post', '/node', 'previous');

    act(() => state().actions.request());
    await waitFor(() => expect(state().loading).toBe(false));

    expect(state().error).toBe(err);
    expect(state().response).toBe('previous');
  });

  it('builds the axios config from method, url, data and headers', async () => {
    request.mockResolvedValueOnce({ data: null });
    const body = { domain: 'robot.dummy', func: 'exec_command', kwargs: {} };
    const headers = { 'X-Trace': 'abc' } as unknown as Map<string, string>;
    const { state } = setup('post', '/node', null, body, headers);

    act(() => state().actions.request());
    await waitFor(() => expect(state().loading).toBe(false));

    expect(request).toHaveBeenCalledTimes(1);
    expect(request.mock.calls[0][0]).toMatchObject({
      url: '/node',
      method: 'post',
      data: body,
      headers: { 'X-Trace': 'abc' },
    });
  });

  it('exposes setResponse to overwrite the stored response', () => {
    const { state } = setup<number>('get', '/count', 0);

    act(() => state().actions.setResponse(42));

    expect(state().response).toBe(42);
  });

  // Known issues in useApi, documented here without changing the source.
  // `it.fails` passes while the bug exists; flip to `it` once fixed.
  it.fails('forwards headers passed as a Map (declared parameter type)', async () => {
    request.mockResolvedValueOnce({ data: null });
    const { state } = setup('get', '/x', null, undefined, new Map([['X-Trace', 'abc']]));

    act(() => state().actions.request());
    await waitFor(() => expect(state().loading).toBe(false));

    expect(request.mock.calls[0][0].headers).toEqual({ 'X-Trace': 'abc' });
  });

  it.fails('applies extra request config (e.g. timeout) passed via ...requestConfig', async () => {
    request.mockResolvedValueOnce({ data: null });
    const { state } = setup('get', '/x', null, undefined, undefined, { timeout: 1000 });

    act(() => state().actions.request());
    await waitFor(() => expect(state().loading).toBe(false));

    expect(request.mock.calls[0][0].timeout).toBe(1000);
  });
});
