// store/conversations.js
import { conversationService } from '@/services/conversationService';

export default {
  state: {
    list: [],
    isLoading: false,
    error: null
  },
  mutations: {
    SET_CONVERSATIONS(state, conversations) {
      state.list = conversations;
    },
    ADD_CONVERSATION(state, conversation) {
      state.list.push(conversation);
    },
    ADD_MESSAGE(state, { conversationId, message }) {
      const conversation = state.list.find(c => c.id === conversationId);
      if (conversation) {
        conversation.messages.push(message);
      }
    },
    UPDATE_CONVERSATION_TITLE(state, { conversationId, title }) {
      const conversation = state.list.find(c => c.id === conversationId);
      if (conversation) {
        conversation.title = title;
      }
    },
    SET_LOADING(state, isLoading) {
      state.isLoading = isLoading;
    },
    SET_ERROR(state, error) {
      state.error = error;
    }
  },
  actions: {
    async fetchConversations({ commit }) {
      commit('SET_LOADING', true);
      try {
        const conversations = await conversationService.getConversations();
        commit('SET_CONVERSATIONS', conversations);
      } catch (error) {
        commit('SET_ERROR', error.message);
        console.error('Failed to fetch conversations:', error);
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async addConversation({ commit }, conversation) {
      try {
        const newConversation = await conversationService.createConversation(conversation);
        commit('ADD_CONVERSATION', newConversation);
        return newConversation;
      } catch (error) {
        commit('SET_ERROR', error.message);
        console.error('Failed to add conversation:', error);
        throw error;
      }
    },
    async addMessageToConversation({ commit }, { conversationId, message }) {
      try {
        const newMessage = await conversationService.sendMessage(conversationId, message);
        commit('ADD_MESSAGE', { conversationId, message: newMessage });
        return newMessage;
      } catch (error) {
        commit('SET_ERROR', error.message);
        console.error('Failed to add message:', error);
        throw error;
      }
    },
    async updateConversationTitle({ commit }, { conversationId, title }) {
      try {
        await conversationService.updateConversationTitle(conversationId, title);
        commit('UPDATE_CONVERSATION_TITLE', { conversationId, title });
      } catch (error) {
        commit('SET_ERROR', error.message);
        console.error('Failed to update conversation title:', error);
        throw error;
      }
    }
  }
};