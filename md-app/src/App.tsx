import { useState } from 'react';
import { Moon, Sun, Dog, Download, Copy, Check } from 'lucide-react';
import MarkdownEditor from './components/MarkdownEditor';
import MarkdownPreview from './components/MarkdownPreview';

const defaultMarkdown = `# Welcome to Markdown Editor

A beautiful, distraction-free writing experience.

## What is Markdown?

Markdown is a lightweight markup language that you can use to add formatting elements to plaintext text documents.

### Why Use Markdown?

- **Simple** - Easy to learn and use
- **Portable** - Files are plain text, readable anywhere
- **Platform Independent** - Create content on any device
- **Future Proof** - Always readable, even without special apps

## Formatting Examples

You can make text **bold** or *italic*, or even ***both***.

### Code

Inline code looks like \`this\`, and code blocks look like:

\`\`\`javascript
function greet(name) {
  return \`Hello, \${name}!\`;
}
\`\`\`

### Lists

Unordered lists:
- First item
- Second item
- Third item

Ordered lists:
1. First step
2. Second step
3. Third step

### Links and More

Check out the [Markdown Guide](https://www.markdownguide.org) for more information.

> "The best way to predict the future is to invent it." - Alan Kay

---

Start writing your own content above. The preview updates in real-time!
`;

function App() {
  const [darkMode, setDarkMode] = useState(true);
  const [markdown, setMarkdown] = useState(defaultMarkdown);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'document.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className={`min-h-screen transition-colors duration-300 ${
      darkMode ? 'bg-gradient-to-br from-black via-zinc-900 to-black' : 'bg-gradient-to-br from-gray-50 via-white to-gray-100'
    }`}>
      <nav className={`fixed top-0 w-full z-50 transition-all duration-300 ${
        darkMode ? 'bg-black/90 border-red-900/50' : 'bg-white/80 border-gray-200'
      } backdrop-blur-lg border-b shadow-sm`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl">
                <img src="/wolf_logo.png" alt="Wolf Logo" className="w-8 h-8" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-red-500 to-red-700 bg-clip-text text-transparent">
                MarkDown
              </span>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handleCopy}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all transform hover:scale-105 ${
                  darkMode
                    ? 'bg-zinc-900 hover:bg-zinc-800 text-red-100 border border-red-900/30'
                    : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                }`}
              >
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                <span className="text-sm font-medium hidden sm:inline">
                  {copied ? 'Copied!' : 'Copy'}
                </span>
              </button>

              <button
                onClick={handleDownload}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all transform hover:scale-105 ${
                  darkMode
                    ? 'bg-zinc-900 hover:bg-zinc-800 text-red-100 border border-red-900/30'
                    : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                }`}
              >
                <Download className="w-4 h-4" />
                <span className="text-sm font-medium hidden sm:inline">Export</span>
              </button>

              <button
                onClick={() => setDarkMode(!darkMode)}
                className={`p-2 rounded-lg transition-all transform hover:scale-105 ${
                  darkMode
                    ? 'bg-zinc-900 hover:bg-zinc-800 border border-red-900/30'
                    : 'bg-gray-100 hover:bg-gray-200'
                }`}
              >
                {darkMode ? <Sun className="w-5 h-5 text-yellow-400" /> : <Moon className="w-5 h-5 text-slate-700" />}
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="pt-24 pb-8 px-4 sm:px-6 lg:px-8 h-screen overflow-hidden">
        <div className="max-w-7xl mx-auto h-full">
          <div className={`grid lg:grid-cols-2 gap-6 h-full rounded-2xl overflow-hidden shadow-2xl ${
            darkMode ? 'bg-zinc-950/80' : 'bg-white/50'
          } backdrop-blur-sm border ${darkMode ? 'border-red-950/50' : 'border-gray-200'}`}>

            <div className="flex flex-col h-full">
              <div className={`px-6 py-4 border-b ${
                darkMode ? 'bg-zinc-900/80 border-red-950/50' : 'bg-gray-50/50 border-gray-200'
              }`}>
                <h2 className="text-sm font-semibold uppercase tracking-wider text-red-500">
                  Editor
                </h2>
              </div>
              <MarkdownEditor
                value={markdown}
                onChange={setMarkdown}
                darkMode={darkMode}
              />
            </div>

            <div className={`flex flex-col h-full border-l ${
              darkMode ? 'border-red-950/50' : 'border-gray-200'
            }`}>
              <div className={`px-6 py-4 border-b ${
                darkMode ? 'bg-zinc-900/80 border-red-950/50' : 'bg-gray-50/50 border-gray-200'
              }`}>
                <h2 className="text-sm font-semibold uppercase tracking-wider text-red-600">
                  Preview
                </h2>
              </div>
              <div className="flex-1 overflow-auto">
                <MarkdownPreview content={markdown} darkMode={darkMode} />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;