<template>
  <header class="header">
    <div class="header-content">
      <div class="header-left">
        <h1 class="header-title">{{ title }}</h1>
      </div>
      
      <div class="header-right">
        <div class="user-info">
          <span class="user-name">{{ user?.name }}</span>
          <button
            @click="logout"
            class="logout-button"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script>
import { computed } from 'vue';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';
import { authService } from '@/services/authService';

export default {
  name: 'Header',
  props: {
    title: {
      type: String,
      required: true
    }
  },
  setup() {
    const store = useStore();
    const router = useRouter();

    const user = computed(() => store.state.auth.user);

    const logout = async () => {
      try {
        await authService.logout();
        store.dispatch('logout');
        router.push('/login');
      } catch (error) {
        console.error('Logout failed:', error);
      }
    };

    return {
      user,
      logout
    };
  }
};
</script>

<style scoped>
.header {
  height: 60px;
  background-color: white;
  border-bottom: 1px solid #e5e5e5;
  padding: 0 24px;
}

.header-content {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1200px;
  margin: 0 auto;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #202123;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-name {
  font-size: 14px;
  color: #343541;
  font-weight: 500;
}

.logout-button {
  padding: 8px 16px;
  background-color: #f3f4f6;
  color: #ef4444;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.logout-button:hover {
  background-color: #fee2e2;
  color: #dc2626;
}
</style>