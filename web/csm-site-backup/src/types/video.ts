export interface Video {
  id: string;
  title: string;
  description?: string;
  category: 'reel' | 'documentary' | 'music' | 'commercial' | 'behind-the-scenes';
  quality?: {
    mobile: string;
    desktop: string;
  };
}

export const videos: Video[] = [
  {
    id: 'o_UitA1xVCE',
    title: 'Behind the Scenes',
    category: 'behind-the-scenes',
    quality: {
      mobile: 'medium',
      desktop: 'hd1080'
    }
  },
  {
    id: 'PfxQSo6285Y',
    title: 'Main Reel',
    category: 'reel',
    quality: {
      mobile: 'medium',
      desktop: 'hd1080'
    }
  },
  {
    id: 'GVNLj1X861s',
    title: 'Documentary Sample',
    category: 'documentary',
    quality: {
      mobile: 'medium',
      desktop: 'hd1080'
    }
  },
  {
    id: '4mPSxZXOHTM',
    title: 'Music Production',
    category: 'music',
    quality: {
      mobile: 'medium',
      desktop: 'hd1080'
    }
  },
  {
    id: 'tKFsTv4devo',
    title: 'Commercial Work',
    category: 'commercial',
    quality: {
      mobile: 'medium',
      desktop: 'hd1080'
    }
  },
  {
    id: '4EUJnaVM7E0',
    title: 'Creative Direction',
    category: 'reel',
    quality: {
      mobile: 'medium',
      desktop: 'hd1080'
    }
  },
  {
    id: 'h_TzBJO6uGg',
    title: 'Music Video',
    category: 'music',
    quality: {
      mobile: 'medium',
      desktop: 'hd1080'
    }
  },
  {
    id: 'Bir9dq6BLms',
    title: 'Commercial Production',
    category: 'commercial',
    quality: {
      mobile: 'medium',
      desktop: 'hd1080'
    }
  }
];