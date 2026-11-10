import './globals.css';
import { ThemeProvider } from '@/components/layout/ThemeProvider';
import { QueryProvider } from '@/components/layout/QueryProvider';

export const metadata = {
  title: 'DeviceStack Technologies | Natural Language Hardware & Firmware Engineering',
  description:
    'Describe your IoT device in plain language and generate verified Arduino firmware, cloud backend, and web interface verified on real boards. One single source-of-truth project spec.',
  keywords: ['IoT', 'Firmware', 'ESP32', 'Arduino', 'Hardware Engineering', 'Embedded AI', 'DeviceStack'],
  authors: [{ name: 'DeviceStack Technologies' }],
  openGraph: {
    title: 'DeviceStack Technologies - Hardware Spec to Deployed Device',
    description: 'Transform plain-language requirements into verified embedded firmware and cloud backends.',
    type: 'website',
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-background text-foreground antialiased selection:bg-primary/20">
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
          <QueryProvider>{children}</QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
