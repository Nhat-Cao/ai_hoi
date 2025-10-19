import { Platform } from 'react-native';

let DEFAULT_BACKEND;

if (Platform.OS === 'android') {
  // Android Emulator dùng địa chỉ đặc biệt
  DEFAULT_BACKEND = 'http://10.0.2.2:8000';
} else if (Platform.OS === 'ios') {
  // iOS simulator truy cập máy thật qua localhost
  DEFAULT_BACKEND = 'http://localhost:8000';
} else {
  // Web hoặc các môi trường khác
  DEFAULT_BACKEND = 'http://127.0.0.1:8000';
}

export async function sendChatMessage(message) {
  const res = await fetch(`${DEFAULT_BACKEND}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  });
  if (!res.ok) throw new Error('Network response was not ok');
  return res.json();
}

export { DEFAULT_BACKEND };