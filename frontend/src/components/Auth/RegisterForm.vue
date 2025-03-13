<template>
  <form @submit.prevent="handleSubmit" class="space-y-6">
    <div>
      <label for="name" class="block text-sm font-medium text-gray-700">
        Full name
      </label>
      <div class="mt-1">
        <input
          id="name"
          v-model="name"
          type="text"
          required
          class="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          :class="{ 'border-red-500': nameError }"
        />
      </div>
      <p v-if="nameError" class="mt-1 text-sm text-red-600">{{ nameError }}</p>
    </div>

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
      <label for="confirmPassword" class="block text-sm font-medium text-gray-700">
        Confirm password
      </label>
      <div class="mt-1">
        <input
          id="confirmPassword"
          v-model="confirmPassword"
          type="password"
          required
          class="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          :class="{ 'border-red-500': confirmPasswordError }"
        />
      </div>
      <p v-if="confirmPasswordError" class="mt-1 text-sm text-red-600">{{ confirmPasswordError }}</p>
    </div>

    <div>
      <button
        type="submit"
        class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        :disabled="isLoading"
      >
        <span v-if="isLoading">Creating account...</span>
        <span v-else>Create account</span>
      </button>
    </div>

    <div class="text-sm text-center">
      <router-link
        to="/login"
        class="font-medium text-blue-600 hover:text-blue-500"
      >
        Already have an account? Sign in
      </router-link>
    </div>
  </form>
</template>

<script>
import { ref, computed } from 'vue';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';
import { authService } from '@/services/authService';
import { validators, getValidationMessage } from '@/utils/validators';

export default {
  name: 'RegisterForm',
  setup() {
    const store = useStore();
    const router = useRouter();
    const name = ref('');
    const email = ref('');
    const password = ref('');
    const confirmPassword = ref('');
    const isLoading = ref(false);

    const nameError = computed(() => {
      if (!name.value) return '';
      return getValidationMessage('name', name.value);
    });

    const emailError = computed(() => {
      if (!email.value) return '';
      return getValidationMessage('email', email.value);
    });

    const passwordError = computed(() => {
      if (!password.value) return '';
      return getValidationMessage('password', password.value);
    });

    const confirmPasswordError = computed(() => {
      if (!confirmPassword.value) return '';
      if (confirmPassword.value !== password.value) {
        return 'Passwords do not match';
      }
      return '';
    });

    const handleSubmit = async () => {
      if (nameError.value || emailError.value || passwordError.value || confirmPasswordError.value) {
        return;
      }

      isLoading.value = true;
      try {
        const user = await authService.register(email.value, password.value, name.value);
        store.dispatch('auth/login', user);
        router.push('/chat');
      } catch (error) {
        console.error('Registration failed:', error);
      } finally {
        isLoading.value = false;
      }
    };

    return {
      name,
      email,
      password,
      confirmPassword,
      isLoading,
      nameError,
      emailError,
      passwordError,
      confirmPasswordError,
      handleSubmit
    };
  }
};
</script> 