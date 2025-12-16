export const SEO_CONFIG = {
  baseUrl: 'https://complexsimplicityai.com',
  defaultTitle: 'Expert 3D Animation & Unreal Engine Development | Complex Simplicity Media',
  defaultDescription: 'Award-winning 3D animation studio specializing in Hollywood productions, game development, and architectural visualization.',
  defaultImage: 'https://s3-media0.fl.yelpcdn.com/bphoto/3Zpn79OBd-1cHWEdQITM9A/o.jpg',
  pages: {
    home: {
      path: '/',
      priority: 1.0,
      changefreq: 'weekly',
      title: 'Expert 3D Animation & Unreal Engine Development | Complex Simplicity Media',
      description: 'Award-winning 3D animation studio with 15+ years experience in Hollywood productions.'
    },
    portfolio: {
      path: '/portfolio',
      priority: 0.9,
      changefreq: 'weekly',
      title: 'Portfolio | Complex Simplicity Media',
      description: 'View our portfolio of professional 3D animation work across film, games, and architectural visualization.'
    },
    services: {
      path: '/services',
      priority: 0.8,
      changefreq: 'monthly',
      title: '3D Animation Services | Complex Simplicity Media',
      description: 'Professional 3D animation services including character animation, VFX, and game development.'
    },
    contact: {
      path: '/contact',
      priority: 0.7,
      changefreq: 'monthly',
      title: 'Contact Us | Complex Simplicity Media',
      description: 'Get in touch with Complex Simplicity Media for professional 3D animation services.'
    },
    ai: {
      path: '/ai',
      priority: 0.9,
      changefreq: 'weekly',
      title: 'AI Integration | Complex Simplicity Media',
      description: 'Experience our advanced AI capabilities for creative and technical solutions.'
    }
  }
} as const;