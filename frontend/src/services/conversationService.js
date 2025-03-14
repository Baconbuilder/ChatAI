import api from './api';

export const conversationService = {
  async getConversations() {
    try {
      const response = await api.get('/conversations');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
      throw this.handleError(error);
    }
  },

  async getConversation(id) {
    try {
      const response = await api.get(`/conversations/${id}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch conversation:', error);
      throw this.handleError(error);
    }
  },

  async createConversation(title) {
    try {
      const response = await api.post('/conversations', { title });
      return response.data;
    } catch (error) {
      console.error('Failed to create conversation:', error);
      throw this.handleError(error);
    }
  },

  async updateConversation(id, data) {
    try {
      const response = await api.put(`/conversations/${id}`, data);
      return response.data;
    } catch (error) {
      console.error('Failed to update conversation:', error);
      throw this.handleError(error);
    }
  },

  async deleteConversation(id) {
    try {
      await api.delete(`/conversations/${id}`);
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      throw this.handleError(error);
    }
  },

  async sendMessage(conversationId, content) {
    try {
      const response = await api.post(`/conversations/${conversationId}/messages`, {
        content
      });
      
      if (!response.data) {
        throw new Error('No response data received from server');
      }
      
      // Ensure the response has the expected structure
      if (!response.data.content) {
        console.warn('Unexpected response structure:', response.data);
        throw new Error('Invalid response format from server');
      }
      
      return response.data;
    } catch (error) {
      console.error('Failed to send message:', error);
      throw this.handleError(error);
    }
  },

  // Helper method to handle errors consistently
  handleError(error) {
    if (error.code === 'ECONNABORTED') {
      return {
        message: 'The request took too long to complete. The system might be busy processing a complex query. Please try again.',
        code: 'TIMEOUT'
      };
    }
    
    if (error.response?.data) {
      return {
        message: error.response.data.detail || error.response.data.message || 'An error occurred with the request.',
        code: error.response.status
      };
    }
    
    if (error.message) {
      return {
        message: error.message,
        code: 'ERROR'
      };
    }
    
    return {
      message: 'An unexpected error occurred.',
      code: 'UNKNOWN'
    };
  }
}; 