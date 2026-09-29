import { apiClient, stage2Config } from './client';
export async function retrieveTransaction(scenario, token) { const { data } = await apiClient.post('/api/v1/simulate/transaction', { scenario }, stage2Config(token)); return data; }
export async function processTransaction(transactionId, token) { const { data } = await apiClient.post(`/api/v1/simulate/transaction/${encodeURIComponent(transactionId)}/process`, null, stage2Config(token)); return data; }
