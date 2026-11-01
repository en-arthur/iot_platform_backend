export default function robots() {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://ai-iot-builder.dev';

  return {
    rules: {
      userAgent: '*',
      allow: '/',
      disallow: ['/app/', '/api/'],
    },
    sitemap: `${baseUrl}/sitemap.xml`,
  };
}
