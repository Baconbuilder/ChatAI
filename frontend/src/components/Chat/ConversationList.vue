<template>
  <div class="flex-1 overflow-y-auto px-4 py-6 sm:px-6">
    <div class="space-y-4">
      <div v-if="messages.length === 0" class="text-center text-gray-500">
        No messages yet. Start a conversation!
      </div>
      <ChatMessage
        v-for="message in messages"
        :key="message.id"
        :message="message"
        :current-user-id="currentUserId"
      />
    </div>
  </div>
</template>

<script>
import { computed } from 'vue';
import { useStore } from 'vuex';
import ChatMessage from './ChatMessage.vue';

export default {
  name: 'ConversationList',
  components: {
    ChatMessage
  },
  props: {
    conversationId: {
      type: String,
      required: true
    }
  },
  setup(props) {
    const store = useStore();

    const messages = computed(() => {
      const conversation = store.state.conversations.list.find(
        c => c.id === props.conversationId
      );
      return conversation?.messages || [];
    });

    const currentUserId = computed(() => store.state.auth.user?.id);

    return {
      messages,
      currentUserId
    };
  }
};
</script> 