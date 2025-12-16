import React from 'react';

export function StructuredData() {
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "ProfessionalService",
    "name": "Complex Simplicity Media",
    "image": "https://s3-media0.fl.yelpcdn.com/bphoto/3Zpn79OBd-1cHWEdQITM9A/o.jpg",
    "description": "Award-winning 3D animation studio specializing in film VFX, game animation, and architectural visualization. 15+ years of experience in major Hollywood productions.",
    "@id": "https://complexsimplicityai.com",
    "url": "https://complexsimplicityai.com",
    "telephone": "+14243330799",
    "address": {
      "@type": "PostalAddress",
      "addressLocality": "Atlanta",
      "addressRegion": "GA",
      "addressCountry": "US"
    },
    "geo": {
      "@type": "GeoCoordinates",
      "latitude": 33.7490,
      "longitude": -84.3880
    },
    "sameAs": [
      "https://www.youtube.com/@GuerradeLosGallos",
      "https://www.youtube.com/@complexs1mplicity",
      "https://www.instagram.com/wolfofallstreets/",
      "https://www.facebook.com/DaveAdams728"
    ],
    "priceRange": "$$$",
    "knowsAbout": [
      "3D Animation",
      "Visual Effects",
      "Character Animation",
      "Motion Graphics",
      "Game Animation",
      "Architectural Visualization"
    ]
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
    />
  );
}