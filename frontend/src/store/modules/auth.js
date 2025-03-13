import { authService } from '@/services/authService';

export default {
  namespaced: true,
  state: {
    user: null,
    token: localStorage.getItem('token') || null
  },
  getters: {
    isAuthenticated: state => !!state.token,
    currentUser: state => state.user
  },
  mutations: {
    SET_USER(state, user) {
      state.user = user;
    },
    SET_TOKEN(state, token) {
      state.token = token;
    },
    CLEAR_AUTH(state) {
      state.user = null;
      state.token = null;
    }
  },
  actions: {
    async login({ commit }, { email, password }) {
      try {
        const response = await authService.login(email, password);
        commit('SET_USER', response.user);
        commit('SET_TOKEN', response.token);
        localStorage.setItem('token', response.token);
        return response.user;
      } catch (error) {
        throw error;
      }
    },
    async logout({ commit }) {
      try {
        await authService.logout();
      } finally {
        commit('CLEAR_AUTH');
        localStorage.removeItem('token');
      }
    },
    async checkAuth({ commit }) {
      try {
        const user = await authService.getCurrentUser();
        if (user) {
          commit('SET_USER', user);
        }
      } catch (error) {
        commit('CLEAR_AUTH');
        localStorage.removeItem('token');
      }
    }
  }
}; 