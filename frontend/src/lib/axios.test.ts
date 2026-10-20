import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const { create, requestUse, responseUse, fakeInstance } = vi.hoisted(() => {
  const requestUse = vi.fn();
  const responseUse = vi.fn();
  const fakeInstance = {
    interceptors: { request: { use: requestUse }, response: { use: responseUse } },
  };
  const create = vi.fn(() => fakeInstance);
  return { create, requestUse, responseUse, fakeInstance };
});

vi.mock('axios', () => ({ default: { create } }));

async function loadInstance() {
  vi.resetModules();
  return (await import('./axios')).default;
}

describe('lib/axios', () => {
  beforeEach(() => {
    create.mockClear();
    requestUse.mockClear();
    responseUse.mockClear();
    vi.stubEnv('NEXT_PUBLIC_API_URL', 'http://api.test/bff');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('creates an instance with the API base URL, timeout and JSON headers', async () => {
    vi.stubEnv('REACT_APP_ENV', 'production');
    const instance = await loadInstance();

    expect(instance).toBe(fakeInstance);
    expect(create).toHaveBeenCalledTimes(1);
    expect(create).toHaveBeenCalledWith({
      baseURL: 'http://api.test/bff',
      timeout: 5000,
      headers: { 'Content-Type': 'application/json', Authorization: '' },
    });
  });

  it('does not register debug interceptors in production', async () => {
    vi.stubEnv('REACT_APP_ENV', 'production');
    await loadInstance();

    expect(requestUse).not.toHaveBeenCalled();
    expect(responseUse).not.toHaveBeenCalled();
  });

  describe('outside production', () => {
    beforeEach(async () => {
      vi.stubEnv('REACT_APP_ENV', 'development');
      await loadInstance();
    });

    it('registers request and response interceptors', () => {
      expect(requestUse).toHaveBeenCalledTimes(1);
      expect(responseUse).toHaveBeenCalledTimes(1);
    });

    it('request interceptor logs and passes the config through', () => {
      const log = vi.spyOn(console, 'log').mockImplementation(() => {});
      const [onFulfilled] = requestUse.mock.calls[0];
      const config = { url: '/node/robot.dummy' };

      expect(onFulfilled(config)).toBe(config);
      expect(log).toHaveBeenCalledWith(config);
    });

    it('request interceptor logs and rejects errors', async () => {
      const log = vi.spyOn(console, 'log').mockImplementation(() => {});
      const [, onRejected] = requestUse.mock.calls[0];
      const error = new Error('request failed');

      await expect(onRejected(error)).rejects.toBe(error);
      expect(log).toHaveBeenCalledWith(error);
    });

    it('response interceptor logs and passes the response through', () => {
      const log = vi.spyOn(console, 'log').mockImplementation(() => {});
      const [onFulfilled] = responseUse.mock.calls[0];
      const response = { status: 200, data: { ok: true } };

      expect(onFulfilled(response)).toBe(response);
      expect(log).toHaveBeenCalledWith(response);
    });

    it('response interceptor logs and rejects errors', async () => {
      const log = vi.spyOn(console, 'log').mockImplementation(() => {});
      const [, onRejected] = responseUse.mock.calls[0];
      const error = new Error('500');

      await expect(onRejected(error)).rejects.toBe(error);
      expect(log).toHaveBeenCalledWith(error);
    });
  });

  it('treats an unset REACT_APP_ENV as non-production', async () => {
    vi.stubEnv('REACT_APP_ENV', undefined);
    await loadInstance();

    expect(requestUse).toHaveBeenCalledTimes(1);
    expect(responseUse).toHaveBeenCalledTimes(1);
  });
});
