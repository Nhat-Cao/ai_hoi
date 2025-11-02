import React, { useState, useRef, useEffect } from 'react';
import { SafeAreaView, StyleSheet } from 'react-native';
import Header from './components/Header';
import MessageList from './components/MessageList';
import MessageInput from './components/MessageInput';
import { sendChatMessage, getUserLocation } from './api';

export default function App() {
  const [messages, setMessages] = useState([{
    id: 'sys',
    role: 'system',
    text: 'Xin chào! Hãy hỏi tôi về món ăn và nhà hàng quanh bạn.'
  }]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [currentLocation, setCurrentLocation] = useState(null);
  const listRef = useRef();

  useEffect(() => {
    listRef.current?.scrollToEnd?.({ animated: true });
  }, [messages]);

  useEffect(() => {
    (async () => {
      const locationData = await getUserLocation();
      const locationStr = locationData.address_details.road + ', ' + locationData.address_details.suburb + ', ' + locationData.address_details.city;
      setCurrentLocation(locationStr);
    })();
  }, []);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg = { id: Date.now().toString(), role: 'user', text: input };
    setMessages(prev => [...prev, userMsg]);
    const msgText = input;
    setInput('');
    setIsSending(true);

    try {
      const data = await sendChatMessage(msgText, currentLocation || "");
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
      <Header currentLocation={currentLocation}/>
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