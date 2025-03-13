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
        v-for="conversation in conversations"
        :key="conversation.id"
        :conversation="conversation"
        :is-active="currentConversationId === conversation.id"
        @select="selectConversation"
        @delete="deleteConversation"
      />
    </div>

    <div class="sidebar-footer">
      <button
        @click="logout"
        class="logout-button"
      >
        Logout
      </button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import ConversationItem from '@/components/Chat/ConversationItem.vue';
import { conversationService } from '@/services/conversationService';

export default {
  name: 'Sidebar',
  components: {
    ConversationItem
  },
  setup() {
    const router = useRouter();
    const conversations = ref([]);
    const currentConversationId = ref(null);

    const loadConversations = async () => {
      try {
        const response = await conversationService.getConversations();
        conversations.value = response;
      } catch (error) {
        console.error('Failed to load conversations:', error);
      }
    };

    const createNewChat = async () => {
      try {
        const conversation = await conversationService.createConversation('New Chat');
        conversations.value.unshift(conversation);
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
        await conversationService.deleteConversation(id);
        conversations.value = conversations.value.filter(c => c.id !== id);
        if (currentConversationId.value === id) {
          router.push('/chat');
        }
      } catch (error) {
        console.error('Failed to delete conversation:', error);
      }
    };

    const logout = () => {
      // Implement logout logic
    };

    onMounted(() => {
      loadConversations();
    });

    return {
      conversations,
      currentConversationId,
      createNewChat,
      selectConversation,
      deleteConversation,
      logout
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

.logout-button {
  width: 100%;
  padding: 12px;
  background-color: #f3f4f6;
  color: #ef4444;
  border: none;
  border-radius: 8px;
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