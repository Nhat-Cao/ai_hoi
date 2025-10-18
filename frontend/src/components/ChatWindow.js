import React from 'react';
import ChatMessage from './ChatMessage';

const ChatWindow = ({ messages }) => {
  return (
    <div className="flex-1 overflow-y-auto pb-32">
      <div className="max-w-4xl mx-auto">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-gray-500">
            <div className="text-center">
              <h1 className="text-4xl font-bold mb-4">AI Hỏi 🍕</h1>
              <p className="text-lg">How can I help you today?</p>
            </div>
          </div>
        ) : (
          messages.map((message, index) => (
            <ChatMessage key={index} message={message} />
          ))
        )}
      </div>
    </div>
  );
};

export default ChatWindow;