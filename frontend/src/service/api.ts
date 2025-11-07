const DEFAULT_BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL;

if (!DEFAULT_BACKEND) {
  throw new Error('NEXT_PUBLIC_BACKEND_URL environment variable is not defined');
}

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

export async function sendChatMessage(text: string, location: string = "") {
  try {
    console.log('Sending request to:', `${DEFAULT_BACKEND}/chat`);
    console.log('Request payload:', { text, location });
    
    const res = await fetch(`${DEFAULT_BACKEND}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, location })
    });
    
    if (!res.ok) {
      const errorData = await res.text();
      console.error('Server error:', errorData);
      throw new Error(`Server error: ${res.status} - ${errorData}`);
    }
    
    return res.json();
  } catch (error) {
    console.error('Network or parsing error:', error);
    throw error;
  }
}

export { DEFAULT_BACKEND };