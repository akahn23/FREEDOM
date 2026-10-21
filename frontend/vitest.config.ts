/** SPDX-License-Identifier: Apache-2.0 */

import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vitest/config';

// Pin the process time zone before any worker starts so local-time based
// formatters (getHours, getDate, ...) are deterministic.
process.env.TZ = 'UTC';

export default defineConfig({
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  test: {
    environment: 'node',
    include: ['src/**/__tests__/**/*.test.ts'],
  },
});
