/** SPDX-License-Identifier: Apache-2.0 */
// @vitest-environment node

import { afterEach, describe, expect, it, vi } from 'vitest';
import { AUTH_CHANNEL, broadcastAuthChanged, subscribeAuthChanged } from '@/lib/auth-events';

type Listener = OmitThisParameter<NonNullable<BroadcastChannel['onmessage']>>;

class FakeBroadcastChannel {
  static instances: FakeBroadcastChannel[] = [];
  readonly listeners = new Set<Listener>();
  readonly postMessage = vi.fn();
  readonly close = vi.fn();
  readonly addEventListener = vi.fn((type: string, fn: Listener) => {
    if (type === 'message') this.listeners.add(fn);
  });
  readonly removeEventListener = vi.fn((type: string, fn: Listener) => {
    if (type === 'message') this.listeners.delete(fn);
  });

  readonly name: string;

  constructor(name: string) {
    this.name = name;
    FakeBroadcastChannel.instances.push(this);
  }

  emit(ev: unknown) {
    for (const fn of this.listeners) fn(ev as MessageEvent);
  }
}

function useFakeChannel() {
  FakeBroadcastChannel.instances = [];
  vi.stubGlobal('BroadcastChannel', FakeBroadcastChannel);
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('AUTH_CHANNEL', () => {
  it('is the shared channel name', () => {
    expect(AUTH_CHANNEL).toBe('freedom-auth');
  });
});

describe('broadcastAuthChanged', () => {
  it('posts an auth-changed message with a timestamp and closes the channel', () => {
    useFakeChannel();
    vi.spyOn(Date, 'now').mockReturnValue(1_700_000_000_000);

    broadcastAuthChanged();

    expect(FakeBroadcastChannel.instances).toHaveLength(1);
    const [ch] = FakeBroadcastChannel.instances;
    expect(ch.name).toBe(AUTH_CHANNEL);
    expect(ch.postMessage).toHaveBeenCalledTimes(1);
    expect(ch.postMessage).toHaveBeenCalledWith({ type: 'auth-changed', at: 1_700_000_000_000 });
    expect(ch.close).toHaveBeenCalledTimes(1);
    expect(ch.postMessage.mock.invocationCallOrder[0]).toBeLessThan(
      ch.close.mock.invocationCallOrder[0],
    );
  });

  it('uses a fresh channel per call', () => {
    useFakeChannel();
    broadcastAuthChanged();
    broadcastAuthChanged();
    expect(FakeBroadcastChannel.instances).toHaveLength(2);
    const [{ at }] = FakeBroadcastChannel.instances[0].postMessage.mock.calls[0];
    expect(typeof at).toBe('number');
  });

  it('does not throw when BroadcastChannel is undefined', () => {
    vi.stubGlobal('BroadcastChannel', undefined);
    expect(() => broadcastAuthChanged()).not.toThrow();
  });

  it('does not throw when the constructor throws', () => {
    vi.stubGlobal(
      'BroadcastChannel',
      class {
        constructor() {
          throw new Error('unsupported');
        }
      },
    );
    expect(() => broadcastAuthChanged()).not.toThrow();
  });

  it('does not throw when postMessage throws', () => {
    vi.stubGlobal(
      'BroadcastChannel',
      class extends FakeBroadcastChannel {
        override readonly postMessage = vi.fn(() => {
          throw new Error('DataCloneError');
        });
      },
    );
    expect(() => broadcastAuthChanged()).not.toThrow();
  });
});

describe('subscribeAuthChanged', () => {
  it('listens on the auth channel and calls onChange for auth-changed messages', () => {
    useFakeChannel();
    const onChange = vi.fn();

    subscribeAuthChanged(onChange);

    const [ch] = FakeBroadcastChannel.instances;
    expect(ch.name).toBe(AUTH_CHANNEL);
    expect(ch.addEventListener).toHaveBeenCalledWith('message', expect.any(Function));

    ch.emit({ data: { type: 'auth-changed', at: 1 } });
    ch.emit({ data: { type: 'auth-changed' } });
    expect(onChange).toHaveBeenCalledTimes(2);
    expect(onChange).toHaveBeenCalledWith();
  });

  it.each([
    ['another type', { data: { type: 'something-else' } }],
    ['a string payload', { data: 'auth-changed' }],
    ['an empty object payload', { data: {} }],
    ['null data', { data: null }],
    ['undefined data', { data: undefined }],
    ['a null event', null],
    ['an undefined event', undefined],
  ])('ignores %s', (_label, ev) => {
    useFakeChannel();
    const onChange = vi.fn();
    subscribeAuthChanged(onChange);

    expect(() => FakeBroadcastChannel.instances[0].emit(ev)).not.toThrow();
    expect(onChange).not.toHaveBeenCalled();
  });

  it('unsubscribe removes the same listener and closes the channel', () => {
    useFakeChannel();
    const onChange = vi.fn();
    const unsubscribe = subscribeAuthChanged(onChange);
    const [ch] = FakeBroadcastChannel.instances;
    const handler = ch.addEventListener.mock.calls[0][1];

    unsubscribe();

    expect(ch.removeEventListener).toHaveBeenCalledWith('message', handler);
    expect(ch.close).toHaveBeenCalledTimes(1);
    expect(ch.listeners.size).toBe(0);
    ch.emit({ data: { type: 'auth-changed' } });
    expect(onChange).not.toHaveBeenCalled();
  });

  it('returns a no-op unsubscribe when BroadcastChannel is undefined', () => {
    vi.stubGlobal('BroadcastChannel', undefined);
    let unsubscribe: (() => void) | undefined;
    expect(() => {
      unsubscribe = subscribeAuthChanged(vi.fn());
    }).not.toThrow();
    expect(typeof unsubscribe).toBe('function');
    expect(unsubscribe?.()).toBeUndefined();
  });

  it('returns a no-op unsubscribe when the constructor throws', () => {
    vi.stubGlobal(
      'BroadcastChannel',
      class {
        constructor() {
          throw new Error('unsupported');
        }
      },
    );
    const onChange = vi.fn();
    const unsubscribe = subscribeAuthChanged(onChange);
    expect(() => unsubscribe()).not.toThrow();
    expect(onChange).not.toHaveBeenCalled();
  });
});

describe('with the runtime BroadcastChannel', () => {
  it('delivers a broadcast to a subscriber on another channel instance', async () => {
    const onChange = vi.fn();
    const unsubscribe = subscribeAuthChanged(onChange);
    try {
      broadcastAuthChanged();
      await vi.waitFor(() => expect(onChange).toHaveBeenCalledTimes(1));
    } finally {
      unsubscribe();
    }
  });
});
