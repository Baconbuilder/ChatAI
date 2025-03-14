// ChatMessage.vue
<template>
  <div
    class="flex"
    :class="{
      'justify-end': isUser,
      'justify-start': !isUser
    }"
  >
    <div
      class="relative rounded-lg px-4 py-2 text-sm max-w-[80%]"
      :class="{
        'bg-blue-600 text-white': isUser,
        'bg-gray-100 text-gray-900': !isUser
      }"
    >
      <div class="whitespace-pre-wrap">{{ message.content }}</div>
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
  margin-bottom: 20px;
  padding: 10px 0;
}

.message.user {
  background-color: #f7f7f8;
}

.message.assistant {
  background-color: white;
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
  flex: 1;
  line-height: 1.6;
}

.message-content pre {
  background-color: #f6f8fa;
  padding: 10px;
  border-radius: 5px;
  overflow: auto;
}

.message-content code {
  font-family: monospace;
}
</style>

