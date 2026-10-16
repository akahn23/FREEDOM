/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

import {getRequestConfig} from 'next-intl/server';
import {hasLocale} from 'next-intl';
import {routing} from './routing';
import {readFile} from 'fs/promises';
import path from 'path';

export default getRequestConfig(async ({requestLocale}) => {
  // Typically corresponds to the `[locale]` segment
  const requested = await requestLocale;
  const locale = hasLocale(routing.locales, requested)
    ? requested
    : routing.defaultLocale;

  return {
    locale,
    // Read at request time (not bundled) so node labels added by scripts/create_node.py
    // show up without rebuilding the frontend image.
    messages: JSON.parse(await readFile(path.join(process.cwd(), 'messages', `${locale}.json`), 'utf-8'))
  };
});
