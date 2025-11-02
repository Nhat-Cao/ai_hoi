import React from 'react';

interface MessageBubbleProps {
  role: 'user' | 'bot';
  text: string;
}

export default function MessageBubble({ role, text }: MessageBubbleProps) {
  return (
    <div className={`my-1.5 p-3 rounded-xl max-w-[85%] shadow-md ${
      role === 'user' 
        ? 'bg-[#6a6b6b] self-end rounded-br-sm' 
        : 'bg-[#1f1f1f] self-start rounded-bl-sm border border-[#2b2b2b]'
    }`}>
      <p className="text-white text-base leading-[22px] white-space-preline">{text}</p>
    </div>
  );
}