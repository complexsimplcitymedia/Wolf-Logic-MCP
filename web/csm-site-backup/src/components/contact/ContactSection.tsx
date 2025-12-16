import React from 'react';
import { ContactInfo } from './ContactInfo';
import { ContactForm } from './ContactForm';

export function ContactSection() {
  return (
    <section id="contact" className="py-24 bg-black/80 backdrop-blur-lg">
      <div className="container mx-auto px-4">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-4xl md:text-5xl font-bold text-center mb-4">Get in Touch</h2>
          <p className="text-xl text-center text-gray-400 mb-12">
            Let's discuss your next project and bring your vision to life
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
            <div className="bg-black/40 backdrop-blur-sm rounded-xl p-8 border border-white/10">
              <h3 className="text-2xl font-bold mb-6">Contact Information</h3>
              <ContactInfo />
            </div>
            
            <div className="bg-black/40 backdrop-blur-sm rounded-xl p-8 border border-white/10">
              <h3 className="text-2xl font-bold mb-6">Send a Message</h3>
              <ContactForm />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}