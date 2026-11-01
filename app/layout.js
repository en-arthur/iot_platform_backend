import './globals.css';
import { ThemeProvider } from '@/components/layout/ThemeProvider';
import { QueryProvider } from '@/components/layout/QueryProvider';

export const metadata = {
  title: 'AI IoT Builder | Natural Language Hardware & Firmware Engineering',
  description:
    'Describe your IoT device in plain language and generate verified firmware, cloud backend, and web interface verified on real boards. One single source-of-truth project spec.',
  keywords: ['IoT', 'Firmware', 'ESP32', 'Hardware Engineering', 'FastAPI', 'Embedded AI', 'Automation'],
  authors: [{ name: 'AI IoT Builder Team' }],
  openGraph: {
    title: 'AI IoT Builder - Hardware Spec to Deployed Device',
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
