import React, { useState, useRef, useEffect } from 'react';
import { SafeAreaView, StyleSheet } from 'react-native';
import Header from './components/Header';
import MessageList from './components/MessageList';
import MessageInput from './components/MessageInput';
import { sendChatMessage } from './api';

export default function App() {
  const [messages, setMessages] = useState([{
    id: 'sys',
    role: 'system',
    text: 'Welcome! Ask me about food and restaurants.'
  }]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const listRef = useRef();

  useEffect(() => {
    listRef.current?.scrollToEnd?.({ animated: true });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg = { id: Date.now().toString(), role: 'user', text: input };
    setMessages(prev => [...prev, userMsg]);
    const msgText = input;
    setInput('');
    setIsSending(true);

    try {
      const data = await sendChatMessage(msgText);
      const botMsg = { id: (Date.now()+1).toString(), role: 'bot', text: data.message || 'No response' };
      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      const errMsg = { id: (Date.now()+2).toString(), role: 'bot', text: 'Error: ' + err.message };
      setMessages(prev => [...prev, errMsg]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <Header />
      <SafeAreaView style={styles.contentWrap}>
        <MessageList messages={messages} listRef={listRef} />
        <MessageInput value={input} onChangeText={setInput} onSend={sendMessage} sending={isSending} />
      </SafeAreaView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#3a3a3aff' },
  contentWrap: { flex: 1, width: '100%', maxWidth: 900, alignSelf: 'center' }
});