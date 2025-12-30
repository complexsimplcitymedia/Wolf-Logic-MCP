import React from 'react';
import { Helmet } from 'react-helmet-async';
import { SEO_CONFIG } from '../../config/seo';

interface SEOHeadProps {
  title?: string;
  description?: string;
  imageUrl?: string;
  path?: string;
  noindex?: boolean;
  keywords?: string[];
}

export function SEOHead({ 
  title = SEO_CONFIG.defaultTitle,
  description = SEO_CONFIG.defaultDescription,
  imageUrl = SEO_CONFIG.defaultImage,
  path = '',
  noindex = false,
  keywords
}: SEOHeadProps) {
  const canonicalUrl = `${SEO_CONFIG.baseUrl}${path}`;

  return (
    <Helmet>
      <title>{title}</title>
      <meta name="description" content={description} />
      {keywords && <meta name="keywords" content={keywords.join(', ')} />}
      <link rel="canonical" href={canonicalUrl} />
      {noindex && <meta name="robots" content="noindex,follow" />}

      {/* Open Graph */}
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:image" content={imageUrl} />
      <meta property="og:url" content={canonicalUrl} />
      <meta property="og:type" content="website" />

      {/* Twitter Cards */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={title} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={imageUrl} />
    </Helmet>
  );
}