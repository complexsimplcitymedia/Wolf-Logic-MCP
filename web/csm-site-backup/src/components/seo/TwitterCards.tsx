import React from 'react';
import { Helmet } from 'react-helmet-async';
import { MetaTagsConfig } from '../../utils/seo/types';

export function TwitterCards({ title, description, imageUrl }: MetaTagsConfig) {
  return (
    <Helmet>
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={title} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={imageUrl} />
    </Helmet>
  );
}