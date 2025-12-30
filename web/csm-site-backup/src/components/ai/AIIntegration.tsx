import React, { useState } from 'react';
import { Send } from 'lucide-react';

export function AIIntegration() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant', content: string }>>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isProcessing) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsProcessing(true);

    try {
      const response = await fetch('http://localhost:11434/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'llama2',
          prompt: userMessage,
          stream: false
        })
      });

      const data = await response.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again.' 
      }]);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <section className="py-16 bg-black/60">
      <div className="container mx-auto px-4">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-8">Try GemOLLama</h2>
          
          <div className="bg-black/40 backdrop-blur-sm rounded-lg border border-white/10 p-4 mb-4 h-96 overflow-y-auto">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`mb-4 ${
                  message.role === 'user' ? 'text-right' : 'text-left'
                }`}
              >
                <div
                  className={`inline-block rounded-lg px-4 py-2 max-w-[80%] ${
                    message.role === 'user'
                      ? 'bg-purple-500/20 text-white'
                      : 'bg-white/10 text-gray-300'
                  }`}
                >
                  {message.content}
                </div>
              </div>
            ))}
            {isProcessing && (
              <div className="text-gray-400 text-center">Processing...</div>
            )}
          </div>

          <form onSubmit={handleSubmit} className="flex gap-4">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask GemOLLama something..."
              className="flex-1 bg-black/40 backdrop-blur-sm rounded-lg border border-white/10 px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500/50"
              disabled={isProcessing}
            />
            <button
              type="submit"
              disabled={isProcessing}
              className="bg-purple-500/20 hover:bg-purple-500/30 text-white px-6 py-2 rounded-lg border border-purple-500/50 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}