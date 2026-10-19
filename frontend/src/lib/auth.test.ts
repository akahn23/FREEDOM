/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

// @vitest-environment node
import type { username } from 'better-auth/plugins';
import { beforeAll, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  betterAuth: vi.fn((config: Record<string, unknown>) => ({ config })),
  Pool: vi.fn(function (this: { opts: unknown }, opts: unknown) {
    this.opts = opts;
  }),
  username: vi.fn((opts: unknown) => ({ id: 'username', opts })),
  admin: vi.fn(() => ({ id: 'admin' })),
  nextCookies: vi.fn(() => ({ id: 'next-cookies' })),
}));

vi.mock('better-auth', () => ({ betterAuth: mocks.betterAuth }));
vi.mock('better-auth/next-js', () => ({ nextCookies: mocks.nextCookies }));
vi.mock('better-auth/plugins', () => ({ username: mocks.username, admin: mocks.admin }));
vi.mock('pg', () => ({ Pool: mocks.Pool }));

type UsernameOptions = NonNullable<Parameters<typeof username>[0]>;

let config: Record<string, any>;
let usernameOptions: UsernameOptions;

beforeAll(async () => {
  vi.stubEnv('DATABASE_URL', 'postgresql://u:p@localhost:5432/freedom');
  vi.stubEnv('BETTER_AUTH_URL', 'http://localhost:3000');
  await import('./auth');
  config = mocks.betterAuth.mock.calls[0][0];
  usernameOptions = mocks.username.mock.calls[0][0] as UsernameOptions;
});

describe('auth server config', () => {
  it('connects to Postgres via DATABASE_URL and uses BETTER_AUTH_URL', () => {
    expect(mocks.Pool).toHaveBeenCalledWith({
      connectionString: 'postgresql://u:p@localhost:5432/freedom',
    });
    expect(config.database).toBeInstanceOf(mocks.Pool);
    expect(config.baseURL).toBe('http://localhost:3000');
  });

  it('uses a 7-day session refreshed daily', () => {
    expect(config.session).toEqual({ expiresIn: 604800, updateAge: 86400 });
  });

  it('enables email/password sign-in but disables self sign-up', () => {
    expect(config.emailAndPassword).toMatchObject({
      enabled: true,
      disableSignUp: true,
      minPasswordLength: 1,
      maxPasswordLength: 128,
    });
  });

  it('registers username, admin and nextCookies plugins', () => {
    expect(config.plugins.map((p: { id: string }) => p.id)).toEqual([
      'username',
      'admin',
      'next-cookies',
    ]);
    expect(usernameOptions).toMatchObject({ minUsernameLength: 1, maxUsernameLength: 30 });
  });
});

describe('usernameValidator', () => {
  it.each([
    ['a', true],
    ['operator01', true],
    ['山田', true],
    ['x'.repeat(30), true],
    ['  admin  ', true],
    ['', false],
    ['   ', false],
    ['x'.repeat(31), false],
    ['john doe', false],
    ['tab\tname', false],
    ['full\u3000width', false],
    ['user@example.com', false],
  ])('%j -> %s', (value, expected) => {
    expect(usernameOptions.usernameValidator!(value)).toBe(expected);
  });

  it('treats null/undefined as empty', () => {
    expect(usernameOptions.usernameValidator!(undefined as unknown as string)).toBe(false);
  });
});
