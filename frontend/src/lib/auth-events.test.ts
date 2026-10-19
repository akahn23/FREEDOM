/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

import { afterEach, describe, expect, it, vi } from 'vitest';
import { AUTH_CHANNEL, broadcastAuthChanged, subscribeAuthChanged } from './auth-events';

/* global EventListener */
type Listener = EventListener;

class FakeBroadcastChannel {
  static instances: FakeBroadcastChannel[] = [];
  listeners = new Set<Listener>();
  postMessage = vi.fn();
  close = vi.fn();
  name: string;

  constructor(name: string) {
    this.name = name;
    FakeBroadcastChannel.instances.push(this);
  }

  addEventListener(_type: 'message', fn: Listener) {
    this.listeners.add(fn);
  }

  removeEventListener(_type: 'message', fn: Listener) {
    this.listeners.delete(fn);
  }

  emit(data: unknown) {
    this.listeners.forEach((fn) => fn({ data } as MessageEvent));
  }
}

function useFakeChannel() {
  FakeBroadcastChannel.instances = [];
  vi.stubGlobal('BroadcastChannel', FakeBroadcastChannel);
}

function useThrowingChannel() {
  vi.stubGlobal(
    'BroadcastChannel',
    vi.fn(function () {
      throw new Error('BroadcastChannel unsupported');
    }),
  );
}

afterEach(() => {
  vi.useRealTimers();
});

describe('broadcastAuthChanged', () => {
  it('posts an auth-changed message on the freedom-auth channel and closes it', () => {
    useFakeChannel();
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-02-10T00:00:00Z'));

    broadcastAuthChanged();

    expect(FakeBroadcastChannel.instances).toHaveLength(1);
    const [ch] = FakeBroadcastChannel.instances;
    expect(ch.name).toBe(AUTH_CHANNEL);
    expect(AUTH_CHANNEL).toBe('freedom-auth');
    expect(ch.postMessage).toHaveBeenCalledWith({
      type: 'auth-changed',
      at: Date.parse('2026-02-10T00:00:00Z'),
    });
    expect(ch.close).toHaveBeenCalledTimes(1);
  });

  it('swallows errors when BroadcastChannel is unavailable', () => {
    useThrowingChannel();
    expect(() => broadcastAuthChanged()).not.toThrow();
  });
});

describe('subscribeAuthChanged', () => {
  it('invokes the callback only for auth-changed messages', () => {
    useFakeChannel();
    const onChange = vi.fn();

    subscribeAuthChanged(onChange);
    const [ch] = FakeBroadcastChannel.instances;
    expect(ch.name).toBe(AUTH_CHANNEL);

    ch.emit({ type: 'something-else' });
    ch.emit(null);
    ch.emit(undefined);
    expect(onChange).not.toHaveBeenCalled();

    ch.emit({ type: 'auth-changed', at: 1 });
    expect(onChange).toHaveBeenCalledTimes(1);
  });

  it('returns an unsubscribe function that detaches the listener and closes the channel', () => {
    useFakeChannel();
    const onChange = vi.fn();

    const unsubscribe = subscribeAuthChanged(onChange);
    const [ch] = FakeBroadcastChannel.instances;
    unsubscribe();

    expect(ch.listeners.size).toBe(0);
    expect(ch.close).toHaveBeenCalledTimes(1);
    ch.emit({ type: 'auth-changed' });
    expect(onChange).not.toHaveBeenCalled();
  });

  it('returns a no-op unsubscribe when BroadcastChannel is unavailable', () => {
    useThrowingChannel();
    const unsubscribe = subscribeAuthChanged(vi.fn());
    expect(typeof unsubscribe).toBe('function');
    expect(() => unsubscribe()).not.toThrow();
  });

  it('receives messages broadcast from another channel instance', async () => {
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
