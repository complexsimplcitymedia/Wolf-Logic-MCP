import { useMemo } from 'react';
import { SEO_CONFIG } from '../config/seo';

interface UseSEOParams {
  path?: string;
  title?: string;
  description?: string;
  imageUrl?: string;
  noindex?: boolean;
}

export function useSEO({
  path = '/',
  title,
  description,
  imageUrl,
  noindex = false
}: UseSEOParams = {}) {
  return useMemo(() => {
    const pageConfig = Object.values(SEO_CONFIG.pages).find(page => page.path === path);
    
    return {
      title: title || pageConfig?.title || SEO_CONFIG.defaultTitle,
      description: description || pageConfig?.description || SEO_CONFIG.defaultDescription,
      imageUrl: imageUrl || SEO_CONFIG.defaultImage,
      canonicalUrl: `${SEO_CONFIG.baseUrl}${path}`,
      noindex
    };
  }, [path, title, description, imageUrl, noindex]);
}