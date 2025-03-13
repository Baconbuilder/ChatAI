import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import store from './store';

// Add a global inactivity timer resetter
const resetInactivityTimer = () => {
  if (store.getters.isAuthenticated) {
    // This event will be caught by App.vue
    window.dispatchEvent(new Event('user-activity'));
  }
};

// Add event listeners
window.addEventListener('mousemove', resetInactivityTimer);
window.addEventListener('keypress', resetInactivityTimer);
window.addEventListener('click', resetInactivityTimer);
window.addEventListener('scroll', resetInactivityTimer);

const app = createApp(App);
app.use(router);
app.use(store);
app.mount('#app');
