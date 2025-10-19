import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Platform,
  KeyboardAvoidingView,
  Animated,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const LINE_HEIGHT = 22;
const PADDING_VERTICAL = 12; // padding top+bottom
const MIN_HEIGHT = 40;
const MAX_HEIGHT = 200;

export default function MessageInput({ value, onChangeText, onSend, sending }) {
  const [inputHeight, setInputHeight] = useState(MIN_HEIGHT);

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={90}
    >
      <View style={styles.container}>
        <View style={styles.innerRow}>
          <TextInput
            id='text-input'
            placeholder="Type a message..."
            placeholderTextColor="#bdbdbd"
            value={value}
            onChangeText={(text) => {
              onChangeText(text);
              const lines = text.split('\n').length;
              const height = Math.min(MAX_HEIGHT, Math.max(MIN_HEIGHT, lines * LINE_HEIGHT + PADDING_VERTICAL));
              setInputHeight(height);
            }}
            multiline={true}
            style={[styles.input, { height: inputHeight }]}
            onContentSizeChange={(e) => {
              setInputHeight(e.nativeEvent.contentSize.height);
            }}
          />

          <TouchableOpacity
            style={[styles.sendBtn, sending && styles.disabled]}
            onPress={onSend}
            disabled={sending}
            activeOpacity={0.8}
          >
            {sending ? (
              <Ionicons
                name="pause"
                size={18}
                color="#0b1b33"
                style={{ transform: [{ rotate: '0deg' }] }}
              />
            ) : (
              <Ionicons
                name="send"
                size={18}
                color="#0b1b33"
                style={{ transform: [{ rotate: '0deg' }] }}
              />
            )}
          </TouchableOpacity>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 10,
    paddingVertical: 10,
  },
  innerRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    backgroundColor: '#161718',
    borderRadius: 30,
    paddingHorizontal: 10,
    paddingVertical: 10,
  },
  inputWrapper: {
    flex: 1,
    justifyContent: 'center',
    borderRadius: 24,
    // no background here — parent has it
  },
  input: {
    flex: 1,
    color: '#fff',
    fontSize: 16,
    lineHeight: 22,
    paddingHorizontal: 8,
    paddingVertical: 6,
    textAlignVertical: 'top', // important for Android
    borderWidth: 0, // turn off border Android
    outlineStyle: 'none', // turn off outline web
    maxHeight: 200,
  },
  sendBtn: {
    backgroundColor: '#f6ac0b', // bright send circle
    borderRadius: 20,
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
    // shadow for mobile
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 2,
  },
  disabled: {
    opacity: 0.6,
  },
});

if (Platform.OS === 'web') {
  const style = document.createElement('style');
  style.innerHTML = `
    textarea::-webkit-scrollbar {
      width: 6px;
    }
    textarea::-webkit-scrollbar-thumb {
      background-color: #f6ac0b;
      border-radius: 4px;
    }
    textarea::-webkit-scrollbar-thumb:hover {
      background-color: #a17007ff;
    }
    textarea::-webkit-scrollbar-track {
      background-color: #161718;
    }
  `;
  document.head.appendChild(style);
}