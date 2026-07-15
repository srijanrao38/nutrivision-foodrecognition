// src/api.ts
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000'; // Django default port

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token && config.headers) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

export default api;
export { API_BASE_URL };
