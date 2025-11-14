import React, { useState, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { DEFAULT_BACKEND } from '@/service/api';
import TypingIndicator from './TypingIndicator';

interface MessageBubbleProps {
  role: 'user' | 'bot';
  text: string;
  isTyping?: boolean;
}

export default function MessageBubble({ role, text, isTyping }: MessageBubbleProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handlePlayAudio = async () => {
    if (isPlaying && audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${DEFAULT_BACKEND}/text-to-speech`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });

      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      
      const audio = new Audio(audioUrl);
      audioRef.current = audio;
      
      audio.onended = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(audioUrl);
      };
      
      await audio.play();
      setIsPlaying(true);
    } catch (error) {
      console.error('Error playing audio:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`my-1.5 rounded-xl max-w-[85%] shadow-md ${
      role === 'user' 
        ? 'bg-orange-400 self-end rounded-br-sm p-3' 
        : 'bg-[#1f1f1f] self-start rounded-bl-sm border border-[#2b2b2b] p-4'
    }`}>
      {isTyping ? (
        <TypingIndicator />
      ) : (
        <>
          {role === 'bot' ? (
            <div className="prose prose-invert max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  // Headings - ChatGPT style
                  h1: ({node, ...props}) => <h1 className="text-2xl font-bold text-white mb-3 mt-4 first:mt-0" {...props} />,
                  h2: ({node, ...props}) => <h2 className="text-xl font-semibold text-white mb-2 mt-4 first:mt-0" {...props} />,
                  h3: ({node, ...props}) => <h3 className="text-lg font-semibold text-gray-100 mb-2 mt-3 first:mt-0" {...props} />,
                  h4: ({node, ...props}) => <h4 className="text-base font-semibold text-gray-100 mb-1 mt-2" {...props} />,
                  
                  // Paragraphs - Better spacing like ChatGPT
                  p: ({node, ...props}) => <p className="text-gray-100 text-[15px] leading-7 mb-3 last:mb-0" {...props} />,
                  
                  // Lists - ChatGPT style with better spacing
                  ul: ({node, ...props}) => <ul className="space-y-1.5 mb-3 pl-1" {...props} />,
                  ol: ({node, ...props}) => <ol className="space-y-1.5 mb-3 pl-1" {...props} />,
                  li: ({node, children, ...props}) => {
                    // Check if parent is ul or ol
                    return (
                      <li className="text-gray-100 text-[15px] leading-7 ml-5 pl-1.5 marker:text-gray-400" {...props}>
                        {children}
                      </li>
                    );
                  },
                  
                  // Emphasis - More subtle like ChatGPT
                  strong: ({node, ...props}) => <strong className="font-semibold text-white" {...props} />,
                  em: ({node, ...props}) => <em className="italic text-gray-200" {...props} />,
                  
                  // Code - ChatGPT style
                  code: ({node, className, children, ...props}) => {
                    const isInline = !className;
                    return isInline ? (
                      <code className="bg-black/40 text-orange-200 px-1.5 py-0.5 rounded text-[14px] font-mono" {...props}>
                        {children}
                      </code>
                    ) : (
                      <code className="block bg-black/40 text-gray-100 p-4 rounded-lg text-[14px] font-mono overflow-x-auto my-3 leading-6" {...props}>
                        {children}
                      </code>
                    );
                  },
                  
                  // Pre blocks
                  pre: ({node, ...props}) => (
                    <pre className="bg-black/40 rounded-lg overflow-hidden my-3" {...props} />
                  ),
                  
                  // Links - ChatGPT style
                  a: ({node, ...props}) => (
                    <a className="text-blue-400 hover:text-blue-300 underline underline-offset-2 transition-colors" target="_blank" rel="noopener noreferrer" {...props} />
                  ),
                  
                  // Blockquote - ChatGPT style
                  blockquote: ({node, ...props}) => (
                    <blockquote className="border-l-2 border-gray-600 pl-4 py-1 italic text-gray-300 my-3 bg-black/20" {...props} />
                  ),
                  
                  // Horizontal rule
                  hr: ({node, ...props}) => <hr className="border-gray-700 my-4" {...props} />,
                  
                  // Tables
                  table: ({node, ...props}) => (
                    <div className="overflow-x-auto my-3">
                      <table className="min-w-full border-collapse" {...props} />
                    </div>
                  ),
                  th: ({node, ...props}) => (
                    <th className="border border-gray-700 px-3 py-2 bg-gray-800/50 text-left font-semibold text-gray-100" {...props} />
                  ),
                  td: ({node, ...props}) => (
                    <td className="border border-gray-700 px-3 py-2 text-gray-200" {...props} />
                  ),
                }}
              >
                {text}
              </ReactMarkdown>
            </div>
          ) : (
            <p className="text-white text-[15px] leading-6 whitespace-pre-line">{text}</p>
          )}
          {role === 'bot' && (
            <button
              onClick={handlePlayAudio}
              disabled={isLoading}
              className="mt-3 p-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed border border-gray-700"
              title={isPlaying ? 'Dừng phát' : 'Nghe nội dung'}
            >
              {isLoading ? (
                <svg className="w-4 h-4 animate-spin text-orange-400" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              ) : isPlaying ? (
                <svg className="w-4 h-4 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                </svg>
              ) : (
                <svg className="w-4 h-4 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                </svg>
              )}
            </button>
          )}
        </>
      )}
    </div>
  );
}
