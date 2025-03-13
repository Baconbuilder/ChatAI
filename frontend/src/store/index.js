// store/index.js
import { createStore } from 'vuex';
import auth from './auth';
import conversations from './conversations';
import { conversationService } from '@/services/conversationService';

export default createStore({
  modules: {
    auth,
    conversations
  },
  state: {
    conversations: {
      list: [],
      current: null
    }
  },
  mutations: {
    setConversations(state, conversations) {
      state.conversations.list = conversations;
    },
    setCurrentConversation(state, conversation) {
      state.conversations.current = conversation;
    },
    addConversation(state, conversation) {
      state.conversations.list.push(conversation);
    }
  },
  actions: {
    async loadConversations({ commit }) {
      try {
        const conversations = await conversationService.getConversations();
        commit('setConversations', conversations);
      } catch (error) {
        console.error('Failed to load conversations:', error);
      }
    }
  }
});

