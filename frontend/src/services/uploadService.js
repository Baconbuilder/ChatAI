import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL;

export const uploadService = {
  async uploadPDF(formData) {
    const response = await axios.post(`${API_URL}/documents/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  }
}; 