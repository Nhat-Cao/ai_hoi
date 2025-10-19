import React from 'react';
import { View, Text, StyleSheet, Platform } from 'react-native';

export default function Header() {
  return (
    <View style={styles.header}>
      <Text style={styles.title}>🍔 Ăn gì? 🍔</Text>
      <Text style={styles.subtitle}>AI Food reviewer</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    paddingTop: Platform.OS === 'web' ? 20 : 12,
    paddingBottom: 12,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderColor: '#3a3a3aff',
    backgroundColor: '#3a3a3aff'
  },
  title: { color: '#fff', fontSize: 18, fontWeight: '700' },
  subtitle: { color: '#bdbdbd', fontSize: 12 }
});
