import api from './api';

export const uploadService = {
  async uploadPDF(formData, conversationId) {
    try {
      formData.append('conversation_id', conversationId);
      
      const response = await api.post('/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          // Authorization header will be added automatically by api.js interceptor
        }
      });
      return response.data;
    } catch (error) {
      console.error('Upload error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      });
      throw error.response?.data || { message: 'Error uploading file' };
    }
  }
}; 