import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000/api',
    headers: {
        'Content-Type': 'application/json',
    },
});

export async function sendQuery(prompt, role = 'Viewer', mode = 'query', db_type = 'nosql') {
    const response = await api.post('/query', { prompt, role, mode, db_type });
    return response.data;
}

export async function getSchema(db_type = 'nosql') {
    const response = await api.get('/schema', { params: { db_type } });
    return response.data;
}

export async function healthCheck() {
    const response = await api.get('/health');
    return response.data;
}

export async function getAuditLogs() {
    const response = await api.get('/audit');
    return response.data;
}

export async function transcribeAudio(audioBlob) {
    const formData = new FormData();
    formData.append('file', audioBlob, 'voice_input.wav');

    const response = await api.post('/transcribe', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
}

export default api;
