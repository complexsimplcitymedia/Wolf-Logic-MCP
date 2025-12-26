interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  darkMode: boolean;
}

function MarkdownEditor({ value, onChange, darkMode }: MarkdownEditorProps) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={`flex-1 w-full px-6 py-6 font-mono text-sm leading-relaxed resize-none focus:outline-none transition-colors ${
        darkMode
          ? 'bg-black/40 text-red-50 placeholder-zinc-600'
          : 'bg-white/30 text-slate-900 placeholder-gray-400'
      }`}
      placeholder="Start typing your markdown here..."
      spellCheck="false"
    />
  );
}

export default MarkdownEditor;
