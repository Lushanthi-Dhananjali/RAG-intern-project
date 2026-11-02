import { API_BASE_URL } from './lessonPlanApi';

export interface UserDto {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserDto;
  message: string;
}

export interface SignupPayload {
  username: string;
  email: string;
  password: string;
  confirm_password: string;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface DbStatusResponse {
  status: string;
  dialect?: string;
  database_url_type?: string;
  registered_users?: number;
  message?: string;
  error?: string;
}

const AUTH_STORAGE_KEY = 'rag_lesson_planner_auth';

export function getStoredAuth(): { token: string | null; user: UserDto | null } {
  if (typeof window === 'undefined') {
    return { token: null, user: null };
  }
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) return { token: null, user: null };
    const parsed = JSON.parse(raw);
    return {
      token: parsed.token || null,
      user: parsed.user || null,
    };
  } catch {
    return { token: null, user: null };
  }
}

export function setStoredAuth(token: string, user: UserDto): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({ token, user }));
  } catch (err) {
    console.error('Failed to save auth to localStorage:', err);
  }
}

export function clearStoredAuth(): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.removeItem(AUTH_STORAGE_KEY);
  } catch (err) {
    console.error('Failed to clear auth storage:', err);
  }
}

export async function signupApi(payload: SignupPayload): Promise<AuthResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || data.message || `Signup failed with status ${response.status}`);
    }

    setStoredAuth(data.access_token, data.user);
    return data;
  } catch (err: any) {
    if (err.message === 'Failed to fetch' || err.name === 'TypeError') {
      throw new Error(
        `Cannot reach backend server at ${API_BASE_URL}. Please ensure your backend is running on port 8000.`
      );
    }
    throw err;
  }
}

export async function loginApi(payload: LoginPayload): Promise<AuthResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || data.message || `Login failed with status ${response.status}`);
    }

    setStoredAuth(data.access_token, data.user);
    return data;
  } catch (err: any) {
    if (err.message === 'Failed to fetch' || err.name === 'TypeError') {
      throw new Error(
        `Cannot reach backend server at ${API_BASE_URL}. Please ensure your backend is running on port 8000.`
      );
    }
    throw err;
  }
}

export async function getCurrentUserApi(): Promise<UserDto> {
  const { token } = getStoredAuth();
  if (!token) {
    throw new Error('No authentication token found.');
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await response.json();
  if (!response.ok) {
    if (response.status === 401 || response.status === 404) {
      clearStoredAuth();
    }
    throw new Error(data.detail || `Failed to fetch user profile: ${response.status}`);
  }

  return data;
}

export async function checkDbStatusApi(): Promise<DbStatusResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/db-status`);
    if (!response.ok) {
      return {
        status: 'error',
        message: `Database status check returned HTTP ${response.status}`,
      };
    }
    return await response.json();
  } catch (err: any) {
    return {
      status: 'error',
      message: 'Backend server is offline on port 8000.',
    };
  }
}
