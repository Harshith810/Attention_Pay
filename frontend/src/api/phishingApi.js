import { apiClient } from './client';
export async function analyzeUrl(url) { const { data } = await apiClient.post('/api/v1/analyze/url', { url }); return data; }
