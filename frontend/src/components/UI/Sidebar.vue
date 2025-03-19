<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <button
        @click="createNewChat"
        class="new-chat-button"
      >
        <span class="new-chat-icon">+</span>
        New Chat
      </button>
    </div>

    <div class="conversations-list">
      <div v-if="conversations.length === 0" class="empty-list">
        No conversations yet
      </div>
      <ConversationItem
        v-for="conversation in sortedConversations"
        :key="conversation.id"
        :conversation="conversation"
        :is-active="currentConversationId === conversation.id"
        @select="selectConversation"
        @delete="deleteConversation"
      />
    </div>

  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useStore } from 'vuex';
import ConversationItem from '@/components/Chat/ConversationItem.vue';

export default {
  name: 'Sidebar',
  components: {
    ConversationItem
  },
  setup() {
    const router = useRouter();
    const store = useStore();
    const currentConversationId = ref(null);

    const conversations = computed(() => store.state.chat.conversations);
    
    // Sort conversations by updated_at timestamp, most recent first
    const sortedConversations = computed(() => {
      return [...conversations.value].sort((a, b) => {
        // Parse dates or use existing Date objects
        const dateA = a.updated_at ? new Date(a.updated_at) : new Date(0);
        const dateB = b.updated_at ? new Date(b.updated_at) : new Date(0);
        // Sort descending (newest first)
        return dateB - dateA;
      });
    });

    const loadConversations = async () => {
      try {
        await store.dispatch('chat/fetchConversations');
      } catch (error) {
        console.error('Failed to load conversations:', error);
      }
    };

    const createNewChat = async () => {
      try {
        const conversation = await store.dispatch('chat/createConversation', 'New Chat');
        router.push(`/chat/${conversation.id}`);
      } catch (error) {
        console.error('Failed to create new chat:', error);
      }
    };

    const selectConversation = (id) => {
      currentConversationId.value = id;
      router.push(`/chat/${id}`);
    };

    const deleteConversation = async (id) => {
      try {
        await store.dispatch('chat/deleteConversation', id);
        if (currentConversationId.value === id) {
          router.push('/chat');
        }
      } catch (error) {
        console.error('Failed to delete conversation:', error);
      }
    };

    onMounted(() => {
      loadConversations();
    });

    return {
      conversations,
      sortedConversations,
      currentConversationId,
      createNewChat,
      selectConversation,
      deleteConversation
    };
  }
};
</script>

<style scoped>
.sidebar {
  width: 280px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #ffffff;
  border-right: 1px solid #e5e5e5;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e5e5e5;
}

.new-chat-button {
  width: 100%;
  padding: 12px;
  background-color: #10a37f;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s ease;
}

.new-chat-button:hover {
  background-color: #0d8a6c;
}

.new-chat-icon {
  font-size: 18px;
  font-weight: 600;
}

.conversations-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.empty-list {
  color: #666;
  text-align: center;
  font-size: 14px;
  padding: 24px;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #e5e5e5;
}

</style>