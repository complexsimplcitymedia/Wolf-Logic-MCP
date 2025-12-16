import { ANIMATION_CATEGORIES, TECH_STACK } from './constants';

export type AnimationCategory = typeof ANIMATION_CATEGORIES[keyof typeof ANIMATION_CATEGORIES];
export type TechStack = typeof TECH_STACK[keyof typeof TECH_STACK];

export interface ProjectDetails {
  title: string;
  description: string;
  category: AnimationCategory;
  technologies: TechStack[];
  image: string;
  videoUrl?: string;
}