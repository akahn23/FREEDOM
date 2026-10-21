/** SPDX-License-Identifier: Apache-2.0 */
// @vitest-environment node

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => {
  const poolCtor = vi.fn();
  class Pool {
    constructor(readonly config: unknown) {
      poolCtor(config);
    }
  }
  return {
    Pool,
    poolCtor,
    betterAuth: vi.fn((options: unknown) => ({ kind: 'auth', options })),
    username: vi.fn((options: unknown) => ({ id: 'username', options })),
    admin: vi.fn(() => ({ id: 'admin' })),
    nextCookies: vi.fn(() => ({ id: 'next-cookies' })),
  };
});

vi.mock('pg', () => ({ Pool: mocks.Pool }));
vi.mock('better-auth', () => ({ betterAuth: mocks.betterAuth }));
vi.mock('better-auth/next-js', () => ({ nextCookies: mocks.nextCookies }));
vi.mock('better-auth/plugins', () => ({ username: mocks.username, admin: mocks.admin }));

// Type taken from the real plugin so the test tracks the better-auth API.
type UsernameValidator = NonNullable<
  NonNullable<Parameters<typeof import('better-auth/plugins').username>[0]>['usernameValidator']
>;

interface UsernameOptions {
  minUsernameLength: number;
  maxUsernameLength: number;
  usernameValidator: UsernameValidator;
}

interface AuthOptions {
  database: unknown;
  baseURL?: string;
  session: { expiresIn: number; updateAge: number };
  emailAndPassword: Record<string, unknown>;
  plugins: Array<{ id: string }>;
}

async function loadAuth() {
  vi.resetModules();
  const mod = await import('@/lib/auth');
  return {
    auth: mod.auth as unknown,
    options: mocks.betterAuth.mock.calls[0][0] as AuthOptions,
    usernameOptions: mocks.username.mock.calls[0][0] as UsernameOptions,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubEnv('DATABASE_URL', 'postgres://user:pass@db.test:5432/freedom');
  vi.stubEnv('BETTER_AUTH_URL', 'http://auth.test');
});

afterEach(() => {
  vi.unstubAllEnvs();
});

describe('auth (better-auth server config)', () => {
  it('creates one pg Pool from DATABASE_URL at import time and passes it as the database', async () => {
    const { options } = await loadAuth();
    expect(mocks.poolCtor).toHaveBeenCalledTimes(1);
    expect(mocks.poolCtor).toHaveBeenCalledWith({
      connectionString: 'postgres://user:pass@db.test:5432/freedom',
    });
    expect(options.database).toBeInstanceOf(mocks.Pool);
  });

  it('exports the object returned by betterAuth', async () => {
    const { auth, options } = await loadAuth();
    expect(mocks.betterAuth).toHaveBeenCalledTimes(1);
    expect(auth).toEqual({ kind: 'auth', options });
  });

  it('uses BETTER_AUTH_URL as baseURL', async () => {
    const { options } = await loadAuth();
    expect(options.baseURL).toBe('http://auth.test');
  });

  it('passes undefined env values through without throwing', async () => {
    vi.stubEnv('DATABASE_URL', undefined);
    vi.stubEnv('BETTER_AUTH_URL', undefined);
    const { options } = await loadAuth();
    expect(mocks.poolCtor).toHaveBeenCalledWith({ connectionString: undefined });
    expect(options.baseURL).toBeUndefined();
  });

  it('keeps sessions for 7 days and refreshes them daily', async () => {
    const { options } = await loadAuth();
    expect(options.session).toEqual({ expiresIn: 604_800, updateAge: 86_400 });
  });

  it('enables email/password sign-in with sign-up disabled', async () => {
    const { options } = await loadAuth();
    expect(options.emailAndPassword).toEqual({
      enabled: true,
      disableSignUp: true,
      minPasswordLength: 1,
      maxPasswordLength: 128,
    });
  });

  it('registers username, admin and nextCookies plugins in that order', async () => {
    const { options } = await loadAuth();
    expect(options.plugins.map((p) => p.id)).toEqual(['username', 'admin', 'next-cookies']);
    expect(mocks.username).toHaveBeenCalledTimes(1);
    expect(mocks.admin).toHaveBeenCalledWith();
    expect(mocks.nextCookies).toHaveBeenCalledWith();
  });

  it('limits usernames to 1-30 characters', async () => {
    const { usernameOptions } = await loadAuth();
    expect(usernameOptions.minUsernameLength).toBe(1);
    expect(usernameOptions.maxUsernameLength).toBe(30);
    expect(usernameOptions.usernameValidator).toBeTypeOf('function');
  });
});

describe('usernameValidator', () => {
  let validate: UsernameValidator;

  beforeEach(async () => {
    validate = (await loadAuth()).usernameOptions.usernameValidator;
  });

  it.each([
    ['a simple name', 'alice'],
    ['a single character', 'a'],
    ['exactly 30 characters', 'a'.repeat(30)],
    ['digits and punctuation', 'user.name_01-x'],
    ['Japanese characters', '山田太郎'],
    ['surrounding spaces (trimmed)', '  alice  '],
    ['30 characters after trimming', ` ${'a'.repeat(30)}\t`],
  ])('accepts %s', (_label, value) => {
    expect(validate(value)).toBe(true);
  });

  it.each([
    ['an empty string', ''],
    ['only spaces', '   '],
    ['31 characters', 'a'.repeat(31)],
    ['an inner space', 'al ice'],
    ['an inner tab', 'al\tice'],
    ['an inner newline', 'al\nice'],
    ['an ideographic space', 'al\u3000ice'],
    ['an email address', 'alice@example.com'],
    ['a lone @', '@'],
    ['a leading @', '@alice'],
  ])('rejects %s', (_label, value) => {
    expect(validate(value)).toBe(false);
  });

  it.each([
    ['null', null],
    ['undefined', undefined],
  ])('rejects %s without throwing', (_label, value) => {
    // Runtime callers may pass null/undefined despite the string signature.
    expect(() => validate(value as unknown as string)).not.toThrow();
    expect(validate(value as unknown as string)).toBe(false);
  });
});
