// ChatInput.vue
<template>
  <div class="border-t border-gray-200 px-4 pt-4 sm:px-6">
    <div class="relative">
      <textarea
        ref="textarea"
        v-model="message"
        rows="3"
        class="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
        placeholder="Type your message..."
        @keydown.enter.prevent="handleEnter"
      ></textarea>
      <div class="absolute inset-y-0 right-0 flex items-center pr-3">
        <button
          type="button"
          class="inline-flex items-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          :disabled="!message.trim() || isLoading"
          @click="sendMessage"
        >
          <span v-if="isLoading">Sending...</span>
          <span v-else>Send</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue';
import { conversationService } from '@/services/conversationService';

export default {
  name: 'ChatInput',
  props: {
    conversationId: {
      type: String,
      required: true
    }
  },
  emits: ['message-sent'],
  setup(props, { emit }) {
    const message = ref('');
    const isLoading = ref(false);
    const textarea = ref(null);

    const handleEnter = (event) => {
      if (event.shiftKey) return;
      sendMessage();
    };

    const sendMessage = async () => {
      if (!message.value.trim() || isLoading.value) return;

      isLoading.value = true;
      try {
        const response = await conversationService.sendMessage(
          props.conversationId,
          message.value.trim()
        );
        emit('message-sent', response);
        message.value = '';
        await nextTick();
        textarea.value?.focus();
      } catch (error) {
        console.error('Failed to send message:', error);
      } finally {
        isLoading.value = false;
      }
    };

    onMounted(() => {
      textarea.value?.focus();
    });

    return {
      message,
      isLoading,
      textarea,
      handleEnter,
      sendMessage
    };
  }
};
</script>

<style scoped>
.chat-input-container {
  padding: 10px 20px;
  background-color: white;
  border-top: 1px solid #e5e5e5;
}

.input-wrapper {
  display: flex;
  position: relative;
}

textarea {
  flex: 1;
  height: 52px;
  max-height: 200px;
  padding: 15px;
  padding-right: 50px;
  border: 1px solid #e5e5e5;
  border-radius: 6px;
  resize: none;
  outline: none;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.5;
}

textarea:focus {
  border-color: #10a37f;
}

.send-button {
  position: absolute;
  right: 10px;
  bottom: 13px;
  background: none;
  border: none;
  color: #10a37f;
  cursor: pointer;
  font-size: 18px;
}

.send-button:disabled {
  color: #d9d9e3;
  cursor: not-allowed;
}

.input-footer {
  margin-top: 5px;
  font-size: 12px;
  color: #8e8ea0;
  text-align: right;
}
</style>