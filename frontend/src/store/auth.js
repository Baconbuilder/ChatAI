// store/auth.js
export default {
    state: {
      user: JSON.parse(localStorage.getItem('user')) || null,
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
      login({ commit }, userData) {
        // In a real app, this would handle API authentication
        commit('SET_USER', userData);
        commit('SET_TOKEN', userData.token);
        
        localStorage.setItem('user', JSON.stringify(userData));
        localStorage.setItem('token', userData.token);
      },
      logout({ commit }) {
        // Clear auth state and local storage
        commit('CLEAR_AUTH');
        localStorage.removeItem('user');
        localStorage.removeItem('token');
      }
        }
    }