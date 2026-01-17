import axios from 'axios';
import { useAuthStore } from './store';

const api = axios.create({
  baseURL: '/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const authApi = {
  register: (data: { email: string; password: string; full_name?: string }) =>
    api.post<{ access_token: string }>('/auth/register', data),
  login: (data: { email: string; password: string }) =>
    api.post<{ access_token: string }>('/auth/login', data),
  me: () => api.get<{ id: string; email: string; full_name: string | null }>('/auth/me'),
};

// Students
export interface Student {
  id: string;
  full_name: string;
  instrument: string;
  level: string;
  parent_email: string | null;
  parent_name: string | null;
  notes: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  lesson_count: number;
}

export const studentsApi = {
  list: (includeArchived = false) =>
    api.get<Student[]>(`/students?include_archived=${includeArchived}`),
  get: (id: string) => api.get<Student>(`/students/${id}`),
  create: (data: {
    full_name: string;
    instrument: string;
    level?: string;
    parent_email?: string;
    parent_name?: string;
    notes?: string;
  }) => api.post<Student>('/students', data),
  update: (id: string, data: Partial<Student>) =>
    api.patch<Student>(`/students/${id}`, data),
  archive: (id: string) => api.post<Student>(`/students/${id}/archive`),
  getInstruments: () => api.get<{ instruments: string[] }>('/students/instruments'),
};

// Lessons
export interface Lesson {
  id: string;
  student_id: string;
  student_name: string;
  lesson_date: string;
  status: string;
  duration_seconds: number | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface Output {
  id: string;
  output_type: string;
  content: string;
  is_edited: boolean;
  is_shared: boolean;
  created_at: string;
}

export interface LessonDetail extends Lesson {
  transcript: string | null;
  outputs: Output[];
}

export const lessonsApi = {
  list: (studentId?: string) =>
    api.get<Lesson[]>(`/lessons${studentId ? `?student_id=${studentId}` : ''}`),
  get: (id: string) => api.get<LessonDetail>(`/lessons/${id}`),
  create: (data: { student_id: string; lesson_date?: string }) =>
    api.post<Lesson>('/lessons', data),
  upload: (id: string, file: File) => {
    const formData = new FormData();
    formData.append('audio', file);
    return api.post<Lesson>(`/lessons/${id}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getStatus: (id: string) =>
    api.get<{ id: string; status: string; error_message: string | null }>(
      `/lessons/${id}/status`
    ),
  process: (id: string) => api.post<Lesson>(`/lessons/${id}/process`),
};

// Outputs
export const outputsApi = {
  get: (id: string) => api.get<Output>(`/outputs/${id}`),
  update: (id: string, content: string) =>
    api.patch<Output>(`/outputs/${id}`, { content }),
  share: (id: string) => api.post<Output>(`/outputs/${id}/share`),
  revert: (id: string) => api.post<Output>(`/outputs/${id}/revert`),
};

export default api;
