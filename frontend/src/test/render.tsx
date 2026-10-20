import type { ReactElement, ReactNode } from 'react';
import { render, type RenderOptions } from '@testing-library/react';
import { NextIntlClientProvider } from 'next-intl';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import messages from '../../messages/ja.json';

const theme = createTheme();

function Providers({ children }: { children: ReactNode }) {
  return (
    <NextIntlClientProvider locale="ja" messages={messages} timeZone="Asia/Tokyo">
      <ThemeProvider theme={theme}>{children}</ThemeProvider>
    </NextIntlClientProvider>
  );
}

export function renderWithProviders(ui: ReactElement, options?: Omit<RenderOptions, 'wrapper'>) {
  return render(ui, { wrapper: Providers, ...options });
}
