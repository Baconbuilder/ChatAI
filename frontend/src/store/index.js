// store/index.js
import { createStore } from 'vuex';
import auth from './auth';
import chat from './modules/chat';
import { conversationService } from '@/services/conversationService';

export default createStore({
  modules: {
    auth,
    chat
  },
  state: {},
  mutations: {},
  actions: {}
});

