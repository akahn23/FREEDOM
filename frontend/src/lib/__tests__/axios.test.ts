/** SPDX-License-Identifier: Apache-2.0 */
// @vitest-environment node

import { AxiosError, type AxiosAdapter, type AxiosInstance, type AxiosResponse } from 'axios';
import { afterEach, beforeEach, describe, expect, it, vi, type MockInstance } from 'vitest';

const API_URL = 'http://api.test';

async function loadInstance(env: string | undefined): Promise<AxiosInstance> {
  vi.stubEnv('NEXT_PUBLIC_API_URL', API_URL);
  vi.stubEnv('REACT_APP_ENV', env);
  vi.resetModules();
  return (await import('@/lib/axios')).default;
}

/** Adapter that answers locally and applies validateStatus like axios' own settle(). */
function fakeAdapter(status: number, data: unknown = { ok: status < 400 }): AxiosAdapter {
  return vi.fn(async (config) => {
    const response: AxiosResponse = {
      data,
      status,
      statusText: String(status),
      headers: {},
      config,
      request: {},
    };
    if (!config.validateStatus || config.validateStatus(status)) return response;
    throw new AxiosError(
      `Request failed with status code ${status}`,
      AxiosError.ERR_BAD_RESPONSE,
      config,
      response.request,
      response,
    );
  });
}

let log: MockInstance<typeof console.log>;

beforeEach(() => {
  log = vi.spyOn(console, 'log').mockImplementation(() => {});
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.restoreAllMocks();
});

describe('axios instance defaults', () => {
  it('uses NEXT_PUBLIC_API_URL, a 5s timeout and JSON headers', async () => {
    const instance = await loadInstance('production');
    expect(instance.defaults.baseURL).toBe(API_URL);
    expect(instance.defaults.timeout).toBe(5000);
    expect(instance.defaults.headers['Content-Type']).toBe('application/json');
    expect(instance.defaults.headers.Authorization).toBe('');
  });

  it('sends the defaults with every request', async () => {
    const instance = await loadInstance('production');
    const adapter = fakeAdapter(200);
    await instance.post('/node/x', { a: 1 }, { adapter });

    const config = vi.mocked(adapter).mock.calls[0][0];
    expect(config.baseURL).toBe(API_URL);
    expect(config.url).toBe('/node/x');
    expect(config.timeout).toBe(5000);
    expect(config.headers.get('Content-Type')).toBe('application/json');
    expect(config.headers.get('Authorization')).toBe('');
    expect(config.data).toBe('{"a":1}');
  });

  it('leaves baseURL undefined when NEXT_PUBLIC_API_URL is not set', async () => {
    vi.stubEnv('NEXT_PUBLIC_API_URL', undefined);
    vi.stubEnv('REACT_APP_ENV', 'production');
    vi.resetModules();
    const instance = (await import('@/lib/axios')).default;
    expect(instance.defaults.baseURL).toBeUndefined();
  });
});

describe('REACT_APP_ENV=production', () => {
  it('registers no interceptors', async () => {
    const instance = await loadInstance('production');
    expect(instance.interceptors.request.handlers).toHaveLength(0);
    expect(instance.interceptors.response.handlers).toHaveLength(0);
  });

  it('resolves successful responses without logging', async () => {
    const instance = await loadInstance('production');
    const res = await instance.get('/ok', { adapter: fakeAdapter(200, { hello: 'world' }) });
    expect(res.status).toBe(200);
    expect(res.data).toEqual({ hello: 'world' });
    expect(log).not.toHaveBeenCalled();
  });

  it('rejects HTTP errors without logging', async () => {
    const instance = await loadInstance('production');
    const err = await instance.get('/boom', { adapter: fakeAdapter(500) }).catch((e: unknown) => e);
    expect(err).toBeInstanceOf(AxiosError);
    expect((err as AxiosError).response?.status).toBe(500);
    expect(log).not.toHaveBeenCalled();
  });
});

describe.each([
  ['development', 'development'],
  ['unset', undefined],
  ['empty', ''],
])('REACT_APP_ENV=%s (non-production)', (_label, env) => {
  it('registers one request and one response interceptor', async () => {
    const instance = await loadInstance(env);
    expect(instance.interceptors.request.handlers).toHaveLength(1);
    expect(instance.interceptors.response.handlers).toHaveLength(1);
  });

  it('logs the request config and the response on success', async () => {
    const instance = await loadInstance(env);
    const res = await instance.get('/ok', { adapter: fakeAdapter(200, { hello: 'world' }) });

    expect(res.data).toEqual({ hello: 'world' });
    expect(log).toHaveBeenCalledTimes(2);
    expect(log.mock.calls[0][0]).toMatchObject({ url: '/ok', baseURL: API_URL, method: 'get' });
    expect(log.mock.calls[1][0]).toBe(res);
  });

  it('logs and re-rejects HTTP errors', async () => {
    const instance = await loadInstance(env);
    const err = await instance.get('/boom', { adapter: fakeAdapter(404) }).catch((e: unknown) => e);

    expect(err).toBeInstanceOf(AxiosError);
    expect((err as AxiosError).response?.status).toBe(404);
    expect(log).toHaveBeenCalledTimes(2);
    expect(log.mock.calls[1][0]).toBe(err);
  });

  it('logs and re-rejects request-phase errors', async () => {
    const instance = await loadInstance(env);
    const failure = new Error('request setup failed');
    // Interceptors added later run first, so this one feeds the module's
    // request error handler.
    instance.interceptors.request.use(() => {
      throw failure;
    });
    const adapter = fakeAdapter(200);

    await expect(instance.get('/never', { adapter })).rejects.toBe(failure);
    expect(adapter).not.toHaveBeenCalled();
    // Logged once by the request error handler and once by the response one.
    expect(log).toHaveBeenCalledTimes(2);
    expect(log).toHaveBeenNthCalledWith(1, failure);
    expect(log).toHaveBeenNthCalledWith(2, failure);
  });

  it('interceptor handlers log and pass values through directly', async () => {
    const instance = await loadInstance(env);
    const [req] = instance.interceptors.request.handlers ?? [];
    const [resp] = instance.interceptors.response.handlers ?? [];
    const error = new Error('x');

    const cfg = { url: '/direct' };
    expect(req.fulfilled(cfg as never)).toBe(cfg);
    await expect(req.rejected?.(error)).rejects.toBe(error);
    const response = { status: 200 };
    expect(resp.fulfilled(response as never)).toBe(response);
    await expect(resp.rejected?.(error)).rejects.toBe(error);
    expect(log.mock.calls.map((c) => c[0])).toEqual([cfg, error, response, error]);
  });
});
