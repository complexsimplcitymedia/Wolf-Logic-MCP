import React from 'react';
import { FooterSection } from './FooterSection';
import { FooterLink } from './FooterLink';
import { 
  Facebook, 
  Instagram, 
  Youtube, 
  Mail, 
  Globe, 
  Phone, 
  MapPin,
  Lightbulb,
  Film,
  Code,
  Gamepad2,
  Bot,
  Terminal,
  Box
} from 'lucide-react';

export function Footer() {
  return (
    <footer className="relative z-10 bg-black/90 backdrop-blur-lg border-t border-white/10">
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Contact Info */}
          <FooterSection title="Contact">
            <div className="space-y-2">
              <div className="flex items-center space-x-2 text-gray-400">
                <MapPin size={14} />
                <span>Atlanta, GA</span>
              </div>
              <div className="flex items-center space-x-2 text-gray-400">
                <Phone size={14} />
                <a href="tel:+18587761198" className="hover:text-white transition-colors duration-300">
                  (858) 776-1198
                </a>
              </div>
              <div className="flex items-center space-x-2 text-gray-400">
                <Mail size={14} />
                <a href="mailto:daviadams@complexsimplicityai.com" className="hover:text-white transition-colors duration-300">
                  daviadams@complexsimplicityai.com
                </a>
              </div>
            </div>
          </FooterSection>

          {/* Services */}
          <FooterSection title="Our Services">
            <div className="grid grid-cols-2 gap-2">
              <FooterLink href="#lighting">
                <div className="flex items-center space-x-1">
                  <Lightbulb size={14} className="text-yellow-500" />
                  <span>Lighting Design</span>
                </div>
              </FooterLink>
              <FooterLink href="#animation">
                <div className="flex items-center space-x-1">
                  <Box size={14} className="text-blue-500" />
                  <span>3D Animation</span>
                </div>
              </FooterLink>
              <FooterLink href="#production">
                <div className="flex items-center space-x-1">
                  <Film size={14} />
                  <span>Film Production</span>
                </div>
              </FooterLink>
              <FooterLink href="#development">
                <div className="flex items-center space-x-1">
                  <Code size={14} />
                  <span>Development</span>
                </div>
              </FooterLink>
              <FooterLink href="https://www.youtube.com/watch?v=4mPSxZXOHTM&list=PLVb2Y8g8UrJd2b1fCv32BdzeWsWEYujKE">
                <div className="flex items-center space-x-1">
                  <Gamepad2 size={14} />
                  <span>Unreal Engine</span>
                </div>
              </FooterLink>
              <FooterLink href="https://llama.complexsimplicityai.com">
                <div className="flex items-center space-x-1">
                  <Bot size={14} />
                  <span>AI Solutions</span>
                </div>
              </FooterLink>
            </div>
          </FooterSection>

          {/* Social Links */}
          <FooterSection title="Connect">
            <div className="grid grid-cols-2 gap-2">
              <FooterLink href="https://www.facebook.com/DaveAdams728">
                <div className="flex items-center space-x-1">
                  <Facebook size={14} />
                  <span>Facebook</span>
                </div>
              </FooterLink>
              <FooterLink href="https://www.instagram.com/wolfofallstreets/">
                <div className="flex items-center space-x-1">
                  <Instagram size={14} />
                  <span>Instagram</span>
                </div>
              </FooterLink>
              <FooterLink href="https://www.youtube.com/@complexs1mplicity">
                <div className="flex items-center space-x-1">
                  <Youtube size={14} />
                  <span>Complex Simplicity</span>
                </div>
              </FooterLink>
              <FooterLink href="https://www.youtube.com/@GuerradeLosGallos">
                <div className="flex items-center space-x-1">
                  <Youtube size={14} />
                  <span>Guerra de Los Gallos</span>
                </div>
              </FooterLink>
              <FooterLink href="https://g.co/kgs/toZLYRc">
                <div className="flex items-center space-x-1">
                  <MapPin size={14} />
                  <span>Location</span>
                </div>
              </FooterLink>
              <FooterLink href="https://complexsimplicityai.com">
                <div className="flex items-center space-x-1">
                  <Globe size={14} />
                  <span>Website</span>
                </div>
              </FooterLink>
            </div>
          </FooterSection>

          {/* Portfolio */}
          <FooterSection title="Portfolio">
            <div className="space-y-2">
              <FooterLink href="https://pro.imdb.com/name/nm17227144?ref_=hm_prof_name">
                Professional Portfolio
              </FooterLink>
            </div>
          </FooterSection>
        </div>

        {/* Copyright */}
        <div className="mt-6 pt-4 border-t border-white/10 text-center text-sm text-gray-400">
          <p>&copy; {new Date().getFullYear()} Complex Simplicity Media. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}