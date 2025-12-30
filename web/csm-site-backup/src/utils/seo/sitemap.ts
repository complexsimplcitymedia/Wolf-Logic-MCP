import { format } from 'date-fns';
import { SITE_PAGES } from './constants';
import type { SitemapConfig } from './types';

export function generateSitemapURLs(): SitemapConfig[] {
  return Object.values(SITE_PAGES).map(({ path, priority, changefreq }) => ({
    path,
    priority,
    changefreq,
    lastmod: new Date()
  }));
}

export function generateSitemapXML(baseURL: string): string {
  const urlset = generateSitemapURLs()
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