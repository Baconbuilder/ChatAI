import api from './api';

export const uploadService = {
  async uploadPDF(formData) {
    try {
      const response = await api.post('/documents/upload', formData);
      return response.data;
    } catch (error) {
      console.error('Upload error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        code: error.code
      });

      if (error.code === 'ECONNABORTED') {
        throw { message: 'Upload timed out. The file might be too large or the server is busy.' };
      }

      throw error.response?.data || { 
        message: 'Error uploading file. Please try again or contact support if the issue persists.' 
      };
    }
  }
}; 