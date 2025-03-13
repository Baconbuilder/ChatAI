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
    ADD_CONVERSATION(state, conversation) {
      state.conversations.unshift(conversation);
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
        commit('SET_CURRENT_CONVERSATION', conversation);
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
    async sendMessage({ commit }, { conversationId, content, language, sourceDocuments }) {
      try {
        commit('SET_LOADING', true);
        const message = await conversationService.sendMessage(
          conversationId,
          content,
          language,
          sourceDocuments
        );
        commit('ADD_MESSAGE', { conversationId, message });
        return message;
      } catch (error) {
        console.error('Error sending message:', error);
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    }
  }
}; 