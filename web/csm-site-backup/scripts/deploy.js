import { execSync } from 'child_process';
import { writeFileSync } from 'fs';
import { generateSitemapXML } from '../src/utils/seo/sitemap';

// Generate sitemap
const sitemap = generateSitemapXML('https://complexsimplicity.org');
writeFileSync('public/sitemap.xml', sitemap);

// Build the project
console.log('Building project...');
execSync('npm run build', { stdio: 'inherit' });

// Deploy to Netlify
console.log('Deploying to Netlify...');
execSync('netlify deploy --prod', { stdio: 'inherit' });