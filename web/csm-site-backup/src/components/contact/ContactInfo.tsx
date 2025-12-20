import React from 'react';
import { Phone, Mail, MapPin, Clock } from 'lucide-react';

interface ContactItemProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  href?: string;
}

function ContactItem({ icon, label, value, href }: ContactItemProps) {
  const content = (
    <div className="flex items-center space-x-3 group">
      <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-white/10 transition-colors duration-300">
        {icon}
      </div>
      <div>
        <p className="text-sm text-gray-400">{label}</p>
        <p className="text-white font-medium">{value}</p>
      </div>
    </div>
  );

  if (href) {
    return (
      <a href={href} className="block" target="_blank" rel="noopener noreferrer">
        {content}
      </a>
    );
  }

  return content;
}

export function ContactInfo() {
  return (
    <div className="space-y-6">
      <ContactItem
        icon={<Phone className="w-5 h-5 text-white/70" />}
        label="Phone"
        value="(424) 333-0799"
        href="tel:+14243330799"
      />
      <ContactItem
        icon={<Mail className="w-5 h-5 text-white/70" />}
        label="Email"
        value="ai-memory@complexsimplicityai.com"
        href="mailto:ai-memory@complexsimplicityai.com"
      />
      <ContactItem
        icon={<MapPin className="w-5 h-5 text-white/70" />}
        label="Location"
        value="Atlanta, GA"
      />
      <ContactItem
        icon={<Clock className="w-5 h-5 text-white/70" />}
        label="Business Hours"
        value="Mon-Fri: 9:00 AM - 6:00 PM EST"
      />
    </div>
  );
}