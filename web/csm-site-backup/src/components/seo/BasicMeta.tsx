import React from 'react';
import { Helmet } from 'react-helmet-async';
import { MetaTagsConfig } from '../../utils/seo/types';

export function BasicMeta({ 
  title, 
  description, 
  canonicalUrl, 
  noindex,
  keywords 
}: MetaTagsConfig) {
  return (
    <Helmet>
      <title>{title}</title>
      <meta name="description" content={description} />
      {keywords && <meta name="keywords" content={keywords.join(', ')} />}
      <link rel="canonical" href={canonicalUrl} />
      {noindex && <meta name="robots" content="noindex,follow" />}
    </Helmet>
  );
}