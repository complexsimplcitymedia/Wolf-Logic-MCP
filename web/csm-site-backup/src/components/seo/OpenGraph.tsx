import React from 'react';
import { Helmet } from 'react-helmet-async';
import { MetaTagsConfig } from '../../utils/seo/types';

export function OpenGraph({ title, description, imageUrl, canonicalUrl }: MetaTagsConfig) {
  return (
    <Helmet>
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:image" content={imageUrl} />
      <meta property="og:url" content={canonicalUrl} />
      <meta property="og:type" content="website" />
    </Helmet>
  );
}