import React, { KeyboardEvent, useRef, useEffect } from 'react';
import { IoSend, IoPause } from "react-icons/io5";

interface MessageInputProps {
  value: string;
  onChangeText: (text: string) => void;
  onSend: () => void;
  sending: boolean;
}

export default function MessageInput({ value, onChangeText, onSend, sending }: MessageInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!sending) {
        onSend();
      }
    }
  };

  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;

    ta.style.height = 'auto';

    const lineHeight = parseInt(getComputedStyle(ta).lineHeight || '20', 10);
    const maxLines = 5;
    const maxHeight = lineHeight * maxLines;

    const newHeight = Math.min(ta.scrollHeight, maxHeight);
    ta.style.height = `${newHeight}px`;

    if (ta.scrollHeight > maxHeight) {
      ta.style.overflowY = 'auto';
    } else {
      ta.style.overflowY = 'hidden';
    }
  }, [value]);

  return (
    <div className="px-3 py-3">
      <div className="relative bg-[#161718] px-4 py-2 shadow-sm border border-[#2a2a2a]
                      rounded-[30px] flex items-end transition-all duration-200">
        <textarea
          ref={textareaRef}
          id="text-input"
          placeholder="Type a message..."
          className="flex-1 bg-transparent text-white text-[15px] resize-none outline-none 
                     placeholder-[#9e9e9e] pr-12 py-2 no-scrollbar"
          value={value}
          onChange={(e) => onChangeText(e.target.value)}
          onKeyPress={handleKeyPress}
          rows={1}
        />

        <button
          className={`absolute right-3 bottom-3 w-8 h-8 flex items-center justify-center rounded-full
                     bg-orange-400 hover:bg-orange-300 transition-all duration-200
                     ${sending ? "opacity-50 cursor-not-allowed" : ""}`}
          onClick={onSend}
          disabled={sending}
        >
          {sending ? (
            <IoPause className="text-[#0b1b33] text-xl" />
          ) : (
            <IoSend className="text-[#0b1b33] text-xl" />
          )}
        </button>
      </div>
    </div>
  );
}
