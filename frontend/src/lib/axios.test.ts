/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AxiosAdapter, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { AxiosError } from 'axios';
import { beforeEach, describe, expect, it, vi } from 'vitest';

async function loadClient(env: Record<string, string | undefined>): Promise<AxiosInstance> {
  vi.resetModules();
  for (const [key, value] of Object.entries(env)) vi.stubEnv(key, value);
  return (await import('./axios')).default;
}

const okAdapter: AxiosAdapter = async (config: InternalAxiosRequestConfig) => ({
  data: { ok: true },
  status: 200,
  statusText: 'OK',
  headers: {},
  config,
});

const failingAdapter: AxiosAdapter = async (config: InternalAxiosRequestConfig) => {
  throw new AxiosError('Request failed with status code 500', 'ERR_BAD_RESPONSE', config);
};

let log: ReturnType<typeof vi.spyOn>;

beforeEach(() => {
  log = vi.spyOn(console, 'log').mockImplementation(() => {});
});

describe('axios client defaults', () => {
  it('uses NEXT_PUBLIC_API_URL as baseURL with a 5s timeout and JSON headers', async () => {
    const client = await loadClient({ NEXT_PUBLIC_API_URL: '/api/bff', REACT_APP_ENV: 'production' });

    expect(client.defaults.baseURL).toBe('/api/bff');
    expect(client.defaults.timeout).toBe(5000);
    expect(client.defaults.headers['Content-Type']).toBe('application/json');
    expect(client.defaults.headers.Authorization).toBe('');
  });

  it('sends requests relative to the BFF base URL', async () => {
    const client = await loadClient({ NEXT_PUBLIC_API_URL: '/api/bff', REACT_APP_ENV: 'production' });
    const adapter = vi.fn(okAdapter);

    const res = await client.post('/node', { domain: 'robot.dummy' }, { adapter });

    expect(res.data).toEqual({ ok: true });
    const sent = adapter.mock.calls[0][0];
    expect(sent.baseURL).toBe('/api/bff');
    expect(sent.url).toBe('/node');
    expect(sent.method).toBe('post');
    expect(sent.data).toBe(JSON.stringify({ domain: 'robot.dummy' }));
    expect(sent.timeout).toBe(5000);
  });
});

describe('debug logging interceptors', () => {
  it('logs request and response outside production', async () => {
    const client = await loadClient({ NEXT_PUBLIC_API_URL: '/api/bff', REACT_APP_ENV: 'development' });

    const res = await client.get('/ping', { adapter: okAdapter });

    expect(log).toHaveBeenCalledTimes(2);
    expect(log.mock.calls[0][0]).toMatchObject({ url: '/ping', method: 'get' });
    expect(log.mock.calls[1][0]).toBe(res);
  });

  it('logs and re-rejects response errors outside production', async () => {
    const client = await loadClient({ NEXT_PUBLIC_API_URL: '/api/bff', REACT_APP_ENV: undefined });

    await expect(client.get('/ping', { adapter: failingAdapter })).rejects.toBeInstanceOf(
      AxiosError,
    );
    expect(log).toHaveBeenCalledTimes(2);
    expect(log.mock.calls[1][0]).toBeInstanceOf(AxiosError);
  });

  it('does not log in production', async () => {
    const client = await loadClient({ NEXT_PUBLIC_API_URL: '/api/bff', REACT_APP_ENV: 'production' });

    await client.get('/ping', { adapter: okAdapter });
    await expect(client.get('/ping', { adapter: failingAdapter })).rejects.toThrow();

    expect(log).not.toHaveBeenCalled();
  });
});
