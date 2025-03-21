// store/index.js
import { createStore } from 'vuex';
import auth from './auth';
import chat from './modules/chat';

export default createStore({
  modules: {
    auth,
    chat
  },
  state: {},
  mutations: {},
  actions: {}
});

