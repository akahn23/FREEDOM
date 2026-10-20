/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

import js from '@eslint/js';
import next from 'eslint-config-next';

export default [
  js.configs.recommended,
  ...next,
  {
    rules: {
      'react/react-in-jsx-scope': 'off',
      // Map/Geoman calls are wrapped in intentional best-effort `try {} catch {}`.
      'no-empty': ['error', { allowEmptyCatch: true }],
      // React Compiler rules (eslint-plugin-react-hooks v7) have pre-existing
      // violations; reported as warnings until the components are refactored.
      'react-hooks/set-state-in-effect': 'warn',
      'react-hooks/refs': 'warn',
      'react-hooks/immutability': 'warn',
    },
  },
  {
    files: ['**/*.ts', '**/*.tsx', '**/*.mts', '**/*.cts'],
    rules: {
      // TypeScript already checks undefined identifiers, and the base
      // no-unused-vars rule misreports type-only names (e.g. params in function types).
      'no-undef': 'off',
      'no-unused-vars': 'off',
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_', caughtErrors: 'none' },
      ],
    },
  },
];
