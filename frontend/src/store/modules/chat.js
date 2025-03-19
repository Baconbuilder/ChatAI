import { conversationService } from '@/services/conversationService';

export default {
  namespaced: true,
  state: {
    conversations: [],
    currentConversation: null,
    isLoading: false
  },
  getters: {
    getConversations: state => state.conversations,
    getCurrentConversation: state => state.currentConversation,
    isLoading: state => state.isLoading
  },
  mutations: {
    SET_CONVERSATIONS(state, conversations) {
      state.conversations = conversations;
    },
    SET_CURRENT_CONVERSATION(state, conversation) {
      state.currentConversation = conversation;
    },
    UPDATE_CONVERSATION_TITLE(state, { conversationId, title }) {
      const conversation = state.conversations.find(c => c.id === conversationId);
      if (conversation) {
        conversation.title = title;
      }
      if (state.currentConversation?.id === conversationId) {
        state.currentConversation.title = title;
      }
    },
    ADD_CONVERSATION(state, conversation) {
      // Ensure the conversation has an updated_at timestamp
      if (!conversation.updated_at) {
        conversation.updated_at = new Date().toISOString();
      }
      state.conversations.unshift(conversation);
      state.currentConversation = conversation;
    },
    REMOVE_CONVERSATION(state, conversationId) {
      state.conversations = state.conversations.filter(c => c.id !== conversationId);
      if (state.currentConversation?.id === conversationId) {
        state.currentConversation = null;
      }
    },
    ADD_MESSAGE(state, { conversationId, message }) {
      if (state.currentConversation?.id === conversationId) {
        if (!state.currentConversation.messages) {
          state.currentConversation.messages = [];
        }
        state.currentConversation.messages.push(message);
        
        // Update the conversation's updated_at timestamp
        state.currentConversation.updated_at = new Date().toISOString();
        
        // Also update in the conversations list
        const conversationInList = state.conversations.find(c => c.id === conversationId);
        if (conversationInList) {
          conversationInList.updated_at = new Date().toISOString();
        }
      }
    },
    REMOVE_MESSAGE(state, { conversationId, messageId }) {
      if (state.currentConversation?.id === conversationId) {
        state.currentConversation.messages = state.currentConversation.messages.filter(
          msg => msg.id !== messageId
        );
      }
    },
    SET_LOADING(state, isLoading) {
      state.isLoading = isLoading;
    }
  },
  actions: {
    async fetchConversations({ commit }) {
      try {
        const conversations = await conversationService.getConversations();
        commit('SET_CONVERSATIONS', conversations);
      } catch (error) {
        console.error('Error fetching conversations:', error);
        throw error;
      }
    },
    async loadConversation({ commit }, conversationId) {
      try {
        const conversation = await conversationService.getConversation(conversationId);
        commit('SET_CURRENT_CONVERSATION', conversation);
        return conversation;
      } catch (error) {
        console.error('Error loading conversation:', error);
        throw error;
      }
    },
    async createConversation({ commit }, title) {
      try {
        const conversation = await conversationService.createConversation(title);
        commit('ADD_CONVERSATION', conversation);
        return conversation;
      } catch (error) {
        console.error('Error creating conversation:', error);
        throw error;
      }
    },
    async deleteConversation({ commit }, conversationId) {
      try {
        await conversationService.deleteConversation(conversationId);
        commit('REMOVE_CONVERSATION', conversationId);
      } catch (error) {
        console.error('Error deleting conversation:', error);
        throw error;
      }
    },
    async sendMessage({ commit }, { conversationId, content, isImageGeneration, isWebSearch }) {
      try {
        const response = await conversationService.sendMessage(conversationId, content, isImageGeneration, isWebSearch);
        return response;
      } catch (error) {
        console.error('Error in sendMessage action:', error);
        throw error;
      }
    },
    async updateConversationTitle({ commit }, { conversationId, title }) {
      try {
        await conversationService.updateConversation(conversationId, { title });
        commit('UPDATE_CONVERSATION_TITLE', { conversationId, title });
      } catch (error) {
        console.error('Error updating conversation title:', error);
        throw error;
      }
    }
  }
}; 