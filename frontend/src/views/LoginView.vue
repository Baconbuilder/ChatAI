// LoginView.vue
<template>
  <div class="auth-container">
    <div class="auth-form">
      <h1>Log in to ChatAI</h1>
      
      <div class="form-group">
        <label for="email">Email</label>
        <input 
          id="email" 
          type="email" 
          v-model="email" 
          placeholder="Enter your email" 
          required
        >
      </div>
      
      <div class="form-group">
        <label for="password">Password</label>
        <input 
          id="password" 
          type="password" 
          v-model="password" 
          placeholder="Enter your password" 
          required
        >
      </div>
      
      <div v-if="error" class="error-message">
        {{ error }}
      </div>
      
      <button 
        @click="login" 
        class="auth-button" 
        :disabled="isLoading"
      >
        {{ isLoading ? 'Logging in...' : 'Log In' }}
      </button>
      
      <div class="auth-footer">
        Don't have an account? 
        <router-link to="/register">Create account</router-link>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../services/api';

export default {
  name: 'LoginView',
  data() {
    return {
      email: '',
      password: '',
      error: '',
      isLoading: false
    }
  },
  methods: {
    async login() {
      if (!this.email || !this.password) {
        this.error = 'Please enter both email and password';
        return;
      }
      
      this.isLoading = true;
      this.error = '';
      
      try {
        // Create form data
        const formData = new FormData();
        formData.append('username', this.email);
        formData.append('password', this.password);
        
        const response = await api.post('/auth/login', formData, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        });
        
        const { access_token, user } = response.data;
        this.$store.dispatch('login', {
          token: access_token,
          ...user
        });
        
        this.$router.push('/');
      } catch (error) {
        this.error = error.response?.data?.detail || 'Login failed. Please try again.';
      } finally {
        this.isLoading = false;
      }
    }
  }
}
</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f9f9f9;
}

.auth-form {
  width: 100%;
  max-width: 400px;
  padding: 30px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

h1 {
  margin-bottom: 30px;
  text-align: center;
  color: #202123;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-size: 14px;
  color: #343541;
}

input {
  width: 100%;
  padding: 12px;
  font-size: 14px;
  border: 1px solid #e5e5e5;
  border-radius: 4px;
  outline: none;
}

input:focus {
  border-color: #10a37f;
}

.auth-button {
  width: 100%;
  padding: 12px;
  background-color: #10a37f;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  margin-bottom: 20px;
}

.auth-button:hover {
  background-color: #0d8a6c;
}

.auth-button:disabled {
  background-color: #a0a0a0;
  cursor: not-allowed;
}

.error-message {
  color: #ff4d4f;
  margin-bottom: 15px;
  font-size: 14px;
}

.auth-footer {
  text-align: center;
  font-size: 14px;
  color: #343541;
}

.auth-footer a {
  color: #10a37f;
  text-decoration: none;
}

.auth-footer a:hover {
  text-decoration: underline;
}
</style>

