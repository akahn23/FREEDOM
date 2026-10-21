/** SPDX-License-Identifier: Apache-2.0 */
// @vitest-environment node

import { describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  createAuthClient: vi.fn((options: unknown) => ({ kind: 'auth-client', options })),
  usernameClient: vi.fn(() => ({ id: 'username-client' })),
  adminClient: vi.fn(() => ({ id: 'admin-client' })),
}));

vi.mock('better-auth/client', () => ({ createAuthClient: mocks.createAuthClient }));
vi.mock('better-auth/client/plugins', () => ({
  usernameClient: mocks.usernameClient,
  adminClient: mocks.adminClient,
}));

describe('authClient', () => {
  it('is created once with the username and admin client plugins, in order', async () => {
    const { authClient } = await import('@/lib/auth-client');

    expect(mocks.createAuthClient).toHaveBeenCalledTimes(1);
    expect(mocks.usernameClient).toHaveBeenCalledWith();
    expect(mocks.adminClient).toHaveBeenCalledWith();

    const options = mocks.createAuthClient.mock.calls[0][0];
    // No baseURL: better-auth falls back to the current origin.
    expect(options).toEqual({
      plugins: [{ id: 'username-client' }, { id: 'admin-client' }],
    });
    expect(authClient as unknown).toEqual({ kind: 'auth-client', options });
  });
});
