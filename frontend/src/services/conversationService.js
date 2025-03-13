import api from './api';

export const conversationService = {
  async getConversations() {
    try {
      const response = await api.get('/conversations');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
      throw error;
    }
  },

  async getConversation(id) {
    try {
      const response = await api.get(`/conversations/${id}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch conversation:', error);
      throw error;
    }
  },

  async createConversation(title) {
    try {
      const response = await api.post('/conversations', { title });
      return response.data;
    } catch (error) {
      console.error('Failed to create conversation:', error);
      throw error;
    }
  },

  async deleteConversation(id) {
    try {
      await api.delete(`/conversations/${id}`);
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      throw error;
    }
  },

  async sendMessage(conversationId, content) {
    try {
      const response = await api.post(`/conversations/${conversationId}/messages`, {
        content
      });
      return response.data;
    } catch (error) {
      console.error('Failed to send message:', error);
      throw error;
    }
  },

  async updateConversationTitle(id, title) {
    try {
      const response = await api.put(`/conversations/${id}`, { title });
      return response.data;
    } catch (error) {
      throw error.response?.data || { message: 'Failed to update conversation title' };
    }
  }
}; 