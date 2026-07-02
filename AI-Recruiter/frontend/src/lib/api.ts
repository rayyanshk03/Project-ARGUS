import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const rankCandidates = async (jobDescription: string, topK: number = 20) => {
  const response = await api.post('/rank', { job_description: jobDescription, top_k: topK });
  return response.data;
};

export const searchCandidates = async (query: string, topK: number = 20) => {
  const response = await api.post('/search', { query, top_k: topK });
  return response.data;
};

export const getCandidate = async (id: string) => {
  const response = await api.get(`/candidate/${id}`);
  return response.data;
};

export const explainCandidate = async (id: string, jobDescription: string) => {
  const response = await api.post(`/explain/${id}`, { job_description: jobDescription });
  return response.data;
};

export const biasCheck = async (jobDescription: string) => {
  const response = await api.post('/bias-check', { job_description: jobDescription });
  return response.data;
};

export const analyzeJD = async (jobDescription: string) => {
  const response = await api.post('/analyze-jd', { job_description: jobDescription });
  return response.data;
};

export const ragQuery = async (query: string) => {
  const response = await api.post('/rag-query', { query });
  return response.data;
};

export const uploadCandidatesFile = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  // Use native fetch to completely bypass Axios's global application/json header,
  // which causes 422 errors, and avoids the boundary stripping issue of manual overrides.
  const response = await fetch(`${API_BASE_URL}/upload-candidates`, {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    throw new Error(`Upload failed with status ${response.status}`);
  }
  return await response.json();
};

export const exportRankings = () => {
  window.open(`${API_BASE_URL}/export`, '_blank');
};

export default api;
