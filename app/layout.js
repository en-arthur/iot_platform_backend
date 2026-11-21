import './globals.css';
import { Space_Grotesk, Inter, JetBrains_Mono } from 'next/font/google';
import { ThemeProvider } from '@/components/layout/ThemeProvider';
import { QueryProvider } from '@/components/layout/QueryProvider';

// Space Grotesk for headings (confident, bold)
const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  weight: ['400', '500', '700'],
  variable: '--font-space-grotesk',
  display: 'swap',
});

// Inter for body text (clean, readable)
const inter = Inter({
  subsets: ['latin'],
  weight: ['400', '500', '700'],
  variable: '--font-inter',
  display: 'swap',
});

// JetBrains Mono for technical bits (code, data, labels)
const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '700'],
  variable: '--font-jetbrains-mono',
  display: 'swap',
});

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
      <head>
        {/* Preconnect to Google Fonts for faster loading */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body 
        className={`min-h-screen bg-background text-foreground antialiased selection:bg-primary/20 ${inter.variable} ${spaceGrotesk.variable} ${jetbrainsMono.variable}`}
      >
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
          <QueryProvider>{children}</QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
