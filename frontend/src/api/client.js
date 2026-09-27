import axios from 'axios';
export const apiClient = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000', timeout: 30000, headers: { 'Content-Type':'application/json' } });
export function stage2Config(token) { return { headers: { 'X-Stage2-Access-Token': token } }; }
