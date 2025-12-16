import { format } from 'date-fns';

export interface SitemapURL {
  path: string;
  priority: number;
  changefreq: 'always' | 'hourly' | 'daily' | 'weekly' | 'monthly' | 'yearly' | 'never';
  lastmod?: Date;
}

export const sitemapURLs: SitemapURL[] = [
  {
    path: '/',
    priority: 1.0,
    changefreq: 'weekly',
    lastmod: new Date()
  },
  {
    path: '/portfolio',
    priority: 0.9,
    changefreq: 'weekly',
    lastmod: new Date()
  },
  {
    path: '/services',
    priority: 0.8,
    changefreq: 'monthly',
    lastmod: new Date()
  },
  {
    path: '/contact',
    priority: 0.7,
    changefreq: 'monthly',
    lastmod: new Date()
  },
  {
    path: '/ai',
    priority: 0.9,
    changefreq: 'weekly',
    lastmod: new Date()
  }
];

export function generateSitemapXML(baseURL: string): string {
  const urlset = sitemapURLs
    .map(({ path, priority, changefreq, lastmod }) => `
      <url>
        <loc>${baseURL}${path}</loc>
        <lastmod>${format(lastmod || new Date(), 'yyyy-MM-dd')}</lastmod>
        <changefreq>${changefreq}</changefreq>
        <priority>${priority.toFixed(1)}</priority>
      </url>
    `)
    .join('');

  return `<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
            http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
      ${urlset}
    </urlset>`;
}