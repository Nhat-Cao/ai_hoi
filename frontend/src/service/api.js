let DEFAULT_BACKEND = 'http://127.0.0.1:8000';

export async function getUserLocation() {
  let coords = null;
    try {
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