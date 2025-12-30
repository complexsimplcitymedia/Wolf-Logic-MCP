export const SEO_CONFIG = {
  title: 'Expert 3D Animation & Unreal Engine Development | Complex Simplicity Media',
  description: 'Award-winning 3D animation studio specializing in Hollywood productions, game development, and architectural visualization.',
  imageUrl: 'https://s3-media0.fl.yelpcdn.com/bphoto/3Zpn79OBd-1cHWEdQITM9A/o.jpg',
  baseUrl: 'https://complexsimplicityai.com'
};

export const SITE_PAGES = {
  HOME: {
    path: '/',
    priority: 1.0,
    changefreq: 'weekly' as const
  },
  PORTFOLIO: {
    path: '/portfolio',
    priority: 0.9,
    changefreq: 'weekly' as const
  },
  SERVICES: {
    path: '/services',
    priority: 0.8,
    changefreq: 'monthly' as const
  },
  CONTACT: {
    path: '/contact',
    priority: 0.7,
    changefreq: 'monthly' as const
  },
  AI: {
    path: '/ai',
    priority: 0.9,
    changefreq: 'weekly' as const
  }
};