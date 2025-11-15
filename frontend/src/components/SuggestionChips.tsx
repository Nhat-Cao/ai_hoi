import React from 'react';

interface SuggestionChipsProps {
  onSelect: (text: string) => void;
  disabled?: boolean;
}

const suggestions = [
  { text: 'Quán phở ngon quanh đây', icon: '🍜' },
  { text: 'Đi ăn gì tối nay?', icon: '🌙' },
  { text: 'Quán ăn sáng ngon', icon: '☀️' },
  { text: 'Tìm quán cafe view đẹp', icon: '☕' },
  { text: 'Món Huế chính gốc', icon: '🥘' },
  { text: 'Buffet nướng giá rẻ', icon: '🍖' },
];

export default function SuggestionChips({ onSelect, disabled }: SuggestionChipsProps) {
  return (
    <div className="py-2 max-w-full">
      <p className="text-gray-500 text-[10px] mb-1">💡 Gợi ý:</p>
      <div className="flex flex-wrap gap-1">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            onClick={() => onSelect(suggestion.text)}
            disabled={disabled}
            className="inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full bg-[#2a2a2a] hover:bg-[#333] text-gray-300 text-[11px] transition-colors disabled:opacity-50 disabled:cursor-not-allowed border border-[#3a3a3a] hover:border-orange-400/50"
          >
            <span className="text-[12px]">{suggestion.icon}</span>
            <span>{suggestion.text}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
