<template>
  <div id="app" @mousemove="resetInactivityTimer" @keypress="resetInactivityTimer">
    <router-view />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';

const store = useStore();
const router = useRouter();
const inactivityTimeout = ref(null);
const inactivityLimit = 3000000; // 30 seconds in milliseconds # actual limit is 30000

const setupInactivityTimer = () => {
  // Only setup timer if user is logged in
  if (store.getters.isAuthenticated) {
    resetInactivityTimer();
  }
};

const resetInactivityTimer = () => {
  // Only reset timer if user is logged in
  if (store.getters.isAuthenticated) {
    clearTimeout(inactivityTimeout.value);
    inactivityTimeout.value = setTimeout(logoutDueToInactivity, inactivityLimit);
  }
};

const logoutDueToInactivity = () => {
  if (store.getters.isAuthenticated) {
    store.dispatch('logout');
    router.push('/login');
    alert('You have been logged out due to inactivity.');
  }
};

// Watch for authentication state changes
watch(
  () => store.getters.isAuthenticated,
  (newVal) => {
    if (newVal) {
      setupInactivityTimer();
    } else {
      clearTimeout(inactivityTimeout.value);
    }
  }
);

onMounted(() => {
  setupInactivityTimer();
});
</script>

<style>
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

body {
  margin: 0;
  padding: 0;
  height: 100vh;
  overflow: hidden;
}
</style>