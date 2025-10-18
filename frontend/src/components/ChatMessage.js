import React from 'react';

const ChatMessage = ({ message }) => {
  const isUser = message.sender === 'user';

  return (
<div className={`flex w-full px-6 py-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
  <div
    className={`text-base p-3 rounded-2xl border break-words whitespace-pre-wrap inline-block
      ${isUser
        ? 'text-gray-800 bg-gray-200 border-gray-300 max-w-[60%]'
        : 'text-gray-700 bg-white border-gray-200'
      }`}
  >
    {message.text}
  </div>
</div>
  );
};

export default ChatMessage;