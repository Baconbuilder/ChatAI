// ChatMessage.vue
<template>
  <div class="message" :class="{
    'user': message.role === 'user',
    'assistant': message.role === 'assistant',
    'error': message.type === 'error'
  }">
    <div class="message-content">
      {{ message.content }}
    </div>
  </div>
</template>

<script>
import { computed } from 'vue';

export default {
  name: 'ChatMessage',
  props: {
    message: {
      type: Object,
      required: true
    },
    currentUserId: {
      type: String,
      required: true
    }
  },
  setup(props) {
    const isUser = computed(() => props.message.userId === props.currentUserId);

    return {
      isUser
    };
  }
};
</script>

<style scoped>
.message {
  display: flex;
  padding: 0.75rem;
  margin: 0.5rem 0;
  border-radius: 12px;
  max-width: 70%;
  position: relative;
  color: #333;
}

.message.user {
  background-color: #f5f5f5;
  margin-left: auto;
  margin-right: 0;
  border: 1px solid #333;
}

.message.assistant {
  background-color: #ffffff;
  border: 1px solid #e0e0e0;
  margin-right: auto;
  margin-left: 0;
}

.message.error {
  margin: 1rem auto;
  background-color: #ffebee;
  color: #d32f2f;
  border: 1px solid #ffcdd2;
  font-size: 0.9em;
  text-align: center;
  max-width: 60%;
}

.message-avatar {
  width: 30px;
  height: 30px;
  margin-right: 15px;
  flex-shrink: 0;
}

.message-avatar img {
  width: 100%;
  height: 100%;
  border-radius: 3px;
  object-fit: cover;
}

.message-content {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.5;
}

.message-content pre {
  background-color: #f6f8fa;
  padding: 10px;
  border-radius: 5px;
  overflow: auto;
  margin: 0.5rem 0;
}

.message-content code {
  font-family: monospace;
  background-color: rgba(0, 0, 0, 0.05);
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-size: 0.9em;
}

/* Add space between consecutive messages */
.message + .message {
  margin-top: 0.75rem;
}
</style>

