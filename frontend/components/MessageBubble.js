import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function MessageBubble({ role, text }) {
  return (
    <View style={[styles.balloon, role === 'user' ? styles.user : styles.bot]}>
      <Text style={styles.text}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  balloon: { marginVertical: 6, padding: 12, borderRadius: 12, maxWidth: '85%', shadowColor: '#000', shadowOpacity: 0.2, shadowRadius: 4, elevation: 2 },
  user: { backgroundColor: '#6a6b6bff', alignSelf: 'flex-end', borderBottomRightRadius: 4 },
  bot: { backgroundColor: '#1f1f1f', alignSelf: 'flex-start', borderBottomLeftRadius: 4, borderWidth: 1, borderColor: '#2b2b2b' },
  text: { color: '#fff', fontSize: 16, lineHeight: 22 },
});