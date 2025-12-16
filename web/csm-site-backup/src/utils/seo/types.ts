export interface MetaTagsConfig {
  title: string;
  description: string;
  canonicalUrl: string;
  imageUrl?: string;
  noindex?: boolean;
  keywords?: string[];
}

export interface SitemapConfig {
  path: string;
  priority: number;
  changefreq: 'always' | 'hourly' | 'daily' | 'weekly' | 'monthly' | 'yearly' | 'never';
  lastmod?: Date;
}