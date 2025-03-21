<template>
  <form @submit.prevent="handleSubmit" class="space-y-6">
    <div>
      <label for="email" class="block text-sm font-medium text-gray-700">
        Email address
      </label>
      <div class="mt-1">
        <input
          id="email"
          v-model="email"
          type="email"
          required
          class="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          :class="{ 'border-red-500': emailError }"
        />
      </div>
      <p v-if="emailError" class="mt-1 text-sm text-red-600">{{ emailError }}</p>
    </div>

    <div>
      <label for="password" class="block text-sm font-medium text-gray-700">
        Password
      </label>
      <div class="mt-1">
        <input
          id="password"
          v-model="password"
          type="password"
          required
          class="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          :class="{ 'border-red-500': passwordError }"
        />
      </div>
      <p v-if="passwordError" class="mt-1 text-sm text-red-600">{{ passwordError }}</p>
    </div>

    <div>
      <button
        type="submit"
        class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        :disabled="isLoading"
      >
        <span v-if="isLoading">Signing in...</span>
        <span v-else>Sign in</span>
      </button>
    </div>

    <div class="text-sm text-center">
      <router-link
        to="/register"
        class="font-medium text-blue-600 hover:text-blue-500"
      >
        Don't have an account? Sign up
      </router-link>
    </div>
  </form>
</template>

<script>
import { ref, computed } from 'vue';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';
import { authService } from '@/services/authService';
import { getValidationMessage } from '@/utils/validators';

export default {
  name: 'LoginForm',
  setup() {
    const store = useStore();
    const router = useRouter();
    const email = ref('');
    const password = ref('');
    const isLoading = ref(false);

    const emailError = computed(() => {
      if (!email.value) return '';
      return getValidationMessage('email', email.value);
    });

    const passwordError = computed(() => {
      if (!password.value) return '';
      return getValidationMessage('password', password.value);
    });

    const handleSubmit = async () => {
      if (emailError.value || passwordError.value) return;

      isLoading.value = true;
      try {
        const user = await authService.login(email.value, password.value);
        store.dispatch('auth/login', user);
        router.push('/chat');
      } catch (error) {
        console.error('Login failed:', error);
      } finally {
        isLoading.value = false;
      }
    };

    return {
      email,
      password,
      isLoading,
      emailError,
      passwordError,
      handleSubmit
    };
  }
};
</script> 