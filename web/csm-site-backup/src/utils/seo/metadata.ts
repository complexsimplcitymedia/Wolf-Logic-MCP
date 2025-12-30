import { keywords } from './keywords';

export const generateMetaTags = () => {
  const allKeywords = Object.values(keywords).flat().join(', ');
  
  return {
    title: `Expert 3D Animation & Unreal Engine Development | Complex Simplicity Media`,
    description: `Award-winning studio specializing in ${keywords.core.join(', ')}. Industry leader in ${keywords.services.join(', ')}. Featured in major Hollywood productions.`,
    keywords: allKeywords
  };
};