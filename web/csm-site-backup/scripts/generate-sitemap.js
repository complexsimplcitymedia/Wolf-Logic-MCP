import { writeFileSync } from 'fs';
import { generateSitemapXML } from '../src/utils/seo/sitemap.js';

const sitemap = generateSitemapXML('https://complexsimplicityai.com');
writeFileSync('public/sitemap.xml', sitemap);

console.log('Sitemap generated successfully!');