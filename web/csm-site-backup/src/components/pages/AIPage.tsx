import React from 'react';
import { Layout } from '../layout/Layout';
import { AIServices } from '../ai/AIServices';
import { AICapabilities } from '../ai/AICapabilities';
import { AIIntegration } from '../ai/AIIntegration';

export function AIPage() {
  return (
    <Layout 
      title="GemOLLama AI | Complex Simplicity Media"
      description="Experience our advanced AI capabilities for creative and technical solutions in 3D animation and visual effects."
    >
      <div className="mt-16">
        <AIServices />
        <AICapabilities />
        <AIIntegration />
      </div>
    </Layout>
  );
}