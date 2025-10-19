import React from 'react';
import { FlatList } from 'react-native';
import MessageBubble from './MessageBubble';

export default function MessageList({ messages, listRef }) {
  return (
    <FlatList
      ref={listRef}
      data={messages}
      renderItem={({ item }) => <MessageBubble role={item.role} text={item.text} />}
      keyExtractor={item => item.id}
      contentContainerStyle={{ padding: 12 }}
    />
  );
}
