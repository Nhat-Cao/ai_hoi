import React from 'react';
import MessageBubble from './MessageBubble';

interface Message {
  id: string;
  role: 'user' | 'bot';
  text: string;
  isTyping?: boolean;
}

interface MessageListProps {
  messages: Message[];
  listRef: React.RefObject<HTMLDivElement | null>;
}

export default function MessageList({ messages, listRef }: MessageListProps) {

  return (
    <div ref={listRef} className="p-3 flex flex-col overflow-y-auto">
      {messages.map((item) => (
        <MessageBubble key={item.id} role={item.role} text={item.text} isTyping={item.isTyping} />
      ))}
    </div>
  );
}