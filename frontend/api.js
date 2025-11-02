import { Platform } from 'react-native';

let DEFAULT_BACKEND;
let Location;

if (Platform.OS === 'android') {
  // Android Emulator dùng địa chỉ đặc biệt
  DEFAULT_BACKEND = 'http://10.0.2.2:8000';
  Location = require("expo-location");
} else if (Platform.OS === 'ios') {
  // iOS simulator truy cập máy thật qua localhost
  DEFAULT_BACKEND = 'http://localhost:8000';
  Location = require("expo-location");
} else {
  // Web hoặc các môi trường khác
  DEFAULT_BACKEND = 'http://127.0.0.1:8000';
}

export async function getUserLocation() {
  let coords = null;
  try {
    if (Platform.OS === "web") {
      coords = await new Promise((resolve, reject) => {
        if ("geolocation" in navigator) {
          navigator.geolocation.getCurrentPosition(
            (pos) => {
              resolve({
                lat: pos.coords.latitude,
                lon: pos.coords.longitude,
              });
            },
            (err) => reject(err)
          );
        } else {
          reject("Geolocation isn't available");
        }
      });
    } else {
      // Mobile
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== "granted") throw "Location permission not granted";
      const loc = await Location.getCurrentPositionAsync({});
      coords = { lat: loc.coords.latitude, lon: loc.coords.longitude};
      console.log("📍 Mobile location coords:", coords);
    }
    const res = await fetch(`${DEFAULT_BACKEND}/location`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(coords)
    });
    return res.json();
  } catch (e) {
    console.error("❌ Geolocation error:", e);
    return null;
  }
}

export async function sendChatMessage(text, location="") {
  const res = await fetch(`${DEFAULT_BACKEND}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, location })
  });
  if (!res.ok) throw new Error('Network response was not ok');
  return res.json();
}

export { DEFAULT_BACKEND };