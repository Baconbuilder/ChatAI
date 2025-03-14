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
  state: {},
  mutations: {},
  actions: {}
});

