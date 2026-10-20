// @vitest-environment node
/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

import { NextRequest } from 'next/server';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  getSession: vi.fn(),
  headers: vi.fn(),
}));

vi.mock('next/headers', () => ({ headers: mocks.headers }));
vi.mock('@/lib/auth', () => ({ auth: { api: { getSession: mocks.getSession } } }));

const BACKEND = 'http://backend.test:9000';
const incomingHeaders = new Headers({ cookie: 'better-auth.session_token=abc' });

type RouteModule = typeof import('./route');
let POST: RouteModule['POST'];
let fetchMock: ReturnType<typeof vi.fn>;

function backendResponse(body: string, init: { status?: number; contentType?: string | null } = {}) {
  const headers = new Headers();
  if (init.contentType !== null) headers.set('content-type', init.contentType ?? 'application/json');
  const res = new Response(body, { status: init.status ?? 200, headers });
  if (init.contentType === null) res.headers.delete('content-type');
  return res;
}

function call(path: string[] | undefined, body: string) {
  const req = new NextRequest(`http://localhost/api/bff/node/${(path ?? []).join('/')}`, {
    method: 'POST',
    body,
  });
  return POST(req, { params: Promise.resolve(path === undefined ? {} : { path }) });
}

function lastFetch() {
  expect(fetchMock).toHaveBeenCalledTimes(1);
  const [url, init] = fetchMock.mock.calls[0] as [string, NonNullable<Parameters<typeof fetch>[1]>];
  return { url, init, headers: init.headers as Record<string, string> };
}

beforeEach(async () => {
  vi.resetModules();
  vi.stubEnv('BACKEND_BASE_URL', BACKEND);
  mocks.headers.mockReset().mockResolvedValue(incomingHeaders);
  mocks.getSession.mockReset().mockResolvedValue(null);
  fetchMock = vi.fn().mockResolvedValue(backendResponse('{"ok":true}'));
  vi.stubGlobal('fetch', fetchMock);
  ({ POST } = await import('./route'));
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe('module config', () => {
  it('runs on the nodejs runtime', async () => {
    const mod = await import('./route');
    expect(mod.runtime).toBe('nodejs');
  });

  it('defaults BACKEND_BASE_URL to http://localhost:8080', async () => {
    vi.resetModules();
    vi.stubEnv('BACKEND_BASE_URL', undefined);
    const mod = await import('./route');
    await mod.POST(
      new NextRequest('http://localhost/api/bff/node/freedom.main', {
        method: 'POST',
        body: '{"func":"fetch_structure"}',
      }),
      { params: Promise.resolve({ path: ['freedom.main'] }) },
    );
    expect(fetchMock.mock.calls[0][0]).toBe('http://localhost:8080/node/freedom.main');
  });
});

describe('request validation', () => {
  it('rejects invalid JSON with 400 invalid_json', async () => {
    const res = await call(['freedom.main'], '{not json');
    expect(res.status).toBe(400);
    expect(await res.json()).toEqual({ error: 'invalid_json' });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it.each(['', '   \n\t'])('treats an empty body (%j) as {} → 400 missing_func', async (body) => {
    const res = await call(['freedom.main'], body);
    expect(res.status).toBe(400);
    expect(await res.json()).toEqual({ error: 'missing_func' });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it.each(['{"kwargs":{}}', '{"func":""}', 'null', '[]', '"fetch_structure"'])(
    'rejects a body without func (%s) with 400 missing_func',
    async (body) => {
      const res = await call(['freedom.main'], body);
      expect(res.status).toBe(400);
      expect(await res.json()).toEqual({ error: 'missing_func' });
      expect(fetchMock).not.toHaveBeenCalled();
      expect(mocks.getSession).not.toHaveBeenCalled();
    },
  );

  // Finding: `func` is only checked for truthiness, so a non-string reaches
  // `func.startsWith(...)` in isGuestAllowed and throws (→ 500) instead of a 400.
  it.fails('rejects a non-string func with 400 instead of throwing', async () => {
    const res = await call(['freedom.log'], '{"func":123}');
    expect(res.status).toBe(400);
  });
});

describe('guest-allowed calls (isGuestAllowed → true)', () => {
  it.each([
    ['freedom.main', 'fetch_structure'],
    ['freedom.log', 'fetch'],
    ['freedom.log', 'fetch_log'],
    ['freedom.log', 'fetch_anything_else'],
  ])('%s/%s is forwarded without a session lookup', async (node, func) => {
    const res = await call([node], JSON.stringify({ func, kwargs: { a: 1 } }));
    expect(res.status).toBe(200);
    expect(mocks.getSession).not.toHaveBeenCalled();
    const { url, init, headers } = lastFetch();
    expect(url).toBe(`${BACKEND}/node/${node}`);
    expect(init.method).toBe('POST');
    expect(headers).toEqual({ 'content-type': 'application/json' });
    expect(JSON.parse(init.body as string)).toEqual({ func, kwargs: { a: 1 } });
  });

  it('forwards a guest call even when a user is logged in, without user headers', async () => {
    mocks.getSession.mockResolvedValue({ user: { id: 'u1', role: 'admin' } });
    await call(['freedom.main'], '{"func":"fetch_structure"}');
    expect(mocks.getSession).not.toHaveBeenCalled();
    expect(lastFetch().headers).toEqual({ 'content-type': 'application/json' });
  });

  it('re-serializes the parsed body (whitespace is not preserved)', async () => {
    await call(['freedom.main'], '  {\n  "func" : "fetch_structure"\n}  ');
    expect(lastFetch().init.body).toBe('{"func":"fetch_structure"}');
  });

  describe('freedom.map/fetch_status (guest, but session-aware)', () => {
    it('looks up the session using the incoming request headers', async () => {
      await call(['freedom.map'], '{"func":"fetch_status"}');
      expect(mocks.headers).toHaveBeenCalled();
      expect(mocks.getSession).toHaveBeenCalledWith({ headers: incomingHeaders });
    });

    it('forwards anonymously when there is no session', async () => {
      const res = await call(['freedom.map'], '{"func":"fetch_status"}');
      expect(res.status).toBe(200);
      expect(lastFetch().headers).toEqual({ 'content-type': 'application/json' });
    });

    it('adds x-user-id and x-user-role for a logged-in user', async () => {
      mocks.getSession.mockResolvedValue({ user: { id: 'u1', role: 'admin' } });
      await call(['freedom.map'], '{"func":"fetch_status"}');
      expect(lastFetch().headers).toEqual({
        'content-type': 'application/json',
        'x-user-id': 'u1',
        'x-user-role': 'admin',
      });
    });

    it.each([null, undefined, ''])('omits x-user-role when role is %j', async (role) => {
      mocks.getSession.mockResolvedValue({ user: { id: 'u1', role } });
      await call(['freedom.map'], '{"func":"fetch_status"}');
      expect(lastFetch().headers).toEqual({ 'content-type': 'application/json', 'x-user-id': 'u1' });
    });

    it('omits x-user-id when the session has no user id', async () => {
      mocks.getSession.mockResolvedValue({ user: { role: 'admin' } });
      await call(['freedom.map'], '{"func":"fetch_status"}');
      expect(lastFetch().headers).toEqual({ 'content-type': 'application/json', 'x-user-role': 'admin' });
    });
  });
});

describe('login-required calls (isGuestAllowed → false)', () => {
  it.each([
    ['freedom.main', 'fetch_status'],
    ['freedom.main', 'update_structure'],
    ['freedom.map', 'fetch_structure'],
    ['freedom.map', 'update_status'],
    ['freedom.log', 'delete_log'],
    ['freedom.log', 'xfetch'],
    ['freedom.log', 'Fetch_log'],
    ['robot.agv', 'fetch_status'],
    ['freedom.main.sub', 'fetch_structure'],
    ['freedom', 'fetch_structure'],
  ])('%s/%s without a session → 403 login_required', async (node, func) => {
    const res = await call([node], JSON.stringify({ func }));
    expect(res.status).toBe(403);
    expect(await res.json()).toEqual({ error: 'login_required' });
    expect(mocks.getSession).toHaveBeenCalledWith({ headers: incomingHeaders });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it.each([{ user: null }, { user: { id: '' } }, { user: { role: 'admin' } }, {}])(
    'denies a session without a user id (%j)',
    async (session) => {
      mocks.getSession.mockResolvedValue(session);
      const res = await call(['robot.agv'], '{"func":"exec_command"}');
      expect(res.status).toBe(403);
      expect(fetchMock).not.toHaveBeenCalled();
    },
  );

  it('forwards an authenticated call with x-user-id only and the raw (trimmed) body', async () => {
    mocks.getSession.mockResolvedValue({ user: { id: 'u42', role: 'admin' } });
    const raw = '  { "func" : "exec_command", "kwargs": {"cmd": "go"} }\n';
    const res = await call(['robot.agv'], raw);
    expect(res.status).toBe(200);
    const { url, init, headers } = lastFetch();
    expect(url).toBe(`${BACKEND}/node/robot.agv`);
    expect(init.method).toBe('POST');
    expect(headers).toEqual({ 'content-type': 'application/json', 'x-user-id': 'u42' });
    expect(init.body).toBe(raw.trim());
  });

  it('joins catch-all path segments with "/"', async () => {
    mocks.getSession.mockResolvedValue({ user: { id: 'u1' } });
    await call(['robot', 'agv'], '{"func":"exec_command"}');
    expect(lastFetch().url).toBe(`${BACKEND}/node/robot/agv`);
  });

  it('applies guest rules to the joined node name only', async () => {
    const res = await call(['freedom', 'main'], '{"func":"fetch_structure"}');
    expect(res.status).toBe(403);
  });

  it('handles a missing path param (node name "")', async () => {
    mocks.getSession.mockResolvedValue({ user: { id: 'u1' } });
    await call(undefined, '{"func":"anything"}');
    expect(lastFetch().url).toBe(`${BACKEND}/node/`);
  });
});

describe('backend response passthrough', () => {
  beforeEach(() => {
    mocks.getSession.mockResolvedValue({ user: { id: 'u1' } });
  });

  it.each([
    [['freedom.main'], 'fetch_structure'],
    [['robot.agv'], 'exec_command'],
  ])('passes body, status and content-type through (%s)', async (path, func) => {
    fetchMock.mockResolvedValue(backendResponse('plain text', { status: 201, contentType: 'text/plain; charset=utf-8' }));
    const res = await call(path, JSON.stringify({ func }));
    expect(res.status).toBe(201);
    expect(res.headers.get('content-type')).toBe('text/plain; charset=utf-8');
    expect(await res.text()).toBe('plain text');
  });

  it.each([
    [['freedom.main'], 'fetch_structure'],
    [['robot.agv'], 'exec_command'],
  ])('defaults content-type to application/json when the backend sends none (%s)', async (path, func) => {
    fetchMock.mockResolvedValue(backendResponse('{"x":1}', { contentType: null }));
    const res = await call(path, JSON.stringify({ func }));
    expect(res.headers.get('content-type')).toBe('application/json');
    expect(await res.json()).toEqual({ x: 1 });
  });

  it.each([
    [['freedom.map'], 'fetch_status', 500, 'boom'],
    [['robot.agv'], 'exec_command', 500, 'robot is not connected'],
    [['robot.agv'], 'exec_command', 404, 'Not Found'],
  ])('propagates backend errors (%s/%s → %i)', async (path, func, status, body) => {
    fetchMock.mockResolvedValue(backendResponse(body, { status, contentType: 'text/plain' }));
    const res = await call(path, JSON.stringify({ func }));
    expect(res.status).toBe(status);
    expect(await res.text()).toBe(body);
  });

  it('lets a network failure reject (no 502 mapping)', async () => {
    fetchMock.mockRejectedValue(new TypeError('fetch failed'));
    await expect(call(['robot.agv'], '{"func":"exec_command"}')).rejects.toThrow('fetch failed');
  });

  it('lets a session lookup failure reject', async () => {
    mocks.getSession.mockRejectedValue(new Error('db down'));
    await expect(call(['robot.agv'], '{"func":"exec_command"}')).rejects.toThrow('db down');
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
