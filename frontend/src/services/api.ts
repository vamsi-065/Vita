const BASE_URL = 'http://localhost:8000/api/v1';

const DEFAULT_EMAIL = 'test@example.com';
const DEFAULT_PASSWORD = 'Password123!';
const DEFAULT_FULL_NAME = 'Test User';
const DEFAULT_BUSINESS_NAME = 'Test Business';

async function authenticate(): Promise<string | null> {
  // 1. Try to login
  try {
    const res = await fetch(`${BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: DEFAULT_EMAIL, password: DEFAULT_PASSWORD })
    });
    if (res.ok) {
      const data = await res.json();
      localStorage.setItem('token', data.access_token);
      return data.access_token;
    }
  } catch (e) {
    console.error('Login failed, trying signup', e);
  }

  // 2. If login fails, try to signup
  try {
    const res = await fetch(`${BASE_URL}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: DEFAULT_EMAIL,
        password: DEFAULT_PASSWORD,
        full_name: DEFAULT_FULL_NAME,
        business_name: DEFAULT_BUSINESS_NAME
      })
    });
    if (res.ok || res.status === 400) { // status 400 might mean user already registered
      // Login again to get token
      const loginRes = await fetch(`${BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: DEFAULT_EMAIL, password: DEFAULT_PASSWORD })
      });
      if (loginRes.ok) {
        const data = await loginRes.json();
        localStorage.setItem('token', data.access_token);
        return data.access_token;
      }
    }
  } catch (e) {
    console.error('Signup failed', e);
  }
  return null;
}

async function getValidToken(): Promise<string | null> {
  let token = localStorage.getItem('token');
  if (!token) {
    token = await authenticate();
  }
  return token;
}

export const api = {
  get: async (endpoint: string, retried = false): Promise<any> => {
    try {
      const token = await getValidToken();
      const headers: Record<string, string> = {
        'Accept': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const res = await fetch(`${BASE_URL}${endpoint}`, {
        method: 'GET',
        headers,
      });

      if (res.status === 401 && !retried) {
        // Token might be expired, clear it and retry once
        localStorage.removeItem('token');
        return api.get(endpoint, true);
      }

      if (!res.ok) throw new Error(`Network response was not ok: ${res.statusText}`);
      return await res.json();
    } catch (e) {
      console.error(`GET request failed for ${endpoint}:`, e);
      return null;
    }
  },

  post: async (endpoint: string, data: any, retried = false): Promise<any> => {
    try {
      const token = await getValidToken();
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const res = await fetch(`${BASE_URL}${endpoint}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(data),
      });

      if (res.status === 401 && !retried) {
        // Token might be expired, clear it and retry once
        localStorage.removeItem('token');
        return api.post(endpoint, data, true);
      }

      if (!res.ok) throw new Error(`Network response was not ok: ${res.statusText}`);
      return await res.json();
    } catch (e) {
      console.error(`POST request failed for ${endpoint}:`, e);
      return null;
    }
  }
};
