<template>
    <div class="chat-container">
      <Sidebar />
      
      <div class="chat-main">
        <Header :title="currentConversation?.title || 'New Conversation'" />
        
        <div class="chat-messages" ref="messagesContainer">
          <div v-if="!currentConversation?.messages?.length" class="empty-chat">
            <div class="empty-chat-content">
              <h2>Welcome to ChatAI</h2>
              <p>Start a new conversation by typing a message below.</p>
              <div class="empty-chat-features">
                <div class="feature">
                  <span class="feature-icon">💬</span>
                  <span>Chat with AI</span>
                </div>
                <div class="feature">
                  <span class="feature-icon">📝</span>
                  <span>Save conversations</span>
                </div>
                <div class="feature">
                  <span class="feature-icon">🔄</span>
                  <span>Access anytime</span>
                </div>
              </div>
            </div>
          </div>
          <ChatMessage 
            v-for="message in currentConversation?.messages"
            :key="message.id" 
            :message="message"
            :current-user-id="currentUserId"
          />
        </div>
        
        <ChatInput @send="handleSendMessage" :is-loading="isLoading" />
      </div>
    </div>
  </template>
  
  <script>
  import { ref, onMounted, watch, computed } from 'vue';
  import { useRoute } from 'vue-router';
  import { useStore } from 'vuex';
  import { conversationService } from '@/services/conversationService';
  import Sidebar from '@/components/UI/Sidebar.vue';
  import Header from '@/components/UI/Header.vue';
  import ChatMessage from '@/components/Chat/ChatMessage.vue';
  import ChatInput from '@/components/Chat/ChatInput.vue';
  
  export default {
    name: 'ChatView',
    components: {
      Sidebar,
      Header,
      ChatMessage,
      ChatInput
    },
    setup() {
      const route = useRoute();
      const store = useStore();
      const currentConversation = ref(null);
      const isLoading = ref(false);
      const messagesContainer = ref(null);

      const currentUserId = computed(() => String(store.state.auth.user?.id));

      const createNewConversation = async (title) => {
        try {
          const response = await conversationService.createConversation(title);
          currentConversation.value = response;
          return response;
        } catch (error) {
          console.error('Failed to create conversation:', error);
          throw error;
        }
      };

      const handleSendMessage = async (content) => {
        if (!content.trim() || isLoading.value) return;
        
        try {
          isLoading.value = true;
          
          // If no conversation exists, create one
          if (!currentConversation.value) {
            await createNewConversation('New Chat');
          }

          // Now send the message
          const response = await conversationService.sendMessage(
            currentConversation.value.id,
            content
          );

          // Initialize messages array if it doesn't exist
          if (!currentConversation.value.messages) {
            currentConversation.value.messages = [];
          }

          // Create user message
          const userMessage = {
            id: Date.now(), // Temporary ID for frontend display
            content: content,
            role: 'user',
            conversation_id: currentConversation.value.id,
            created_at: new Date().toISOString()
          };

          // Add user message and assistant response
          currentConversation.value.messages.push(userMessage);
          currentConversation.value.messages.push(response);
          
          // Update conversation title if it's the first message
          if (currentConversation.value.messages.length === 1) {
            const newTitle = content.length > 30 
              ? content.substring(0, 30) + '...' 
              : content;
            currentConversation.value.title = newTitle;
          }

          scrollToBottom();
        } catch (error) {
          console.error('Error sending message:', error);
        } finally {
          isLoading.value = false;
        }
      };

      const loadConversation = async (id) => {
        if (!id) return;
        try {
          const response = await conversationService.getConversation(id);
          currentConversation.value = response;
          scrollToBottom();
        } catch (error) {
          console.error('Failed to load conversation:', error);
        }
      };

      const scrollToBottom = () => {
        setTimeout(() => {
          if (messagesContainer.value) {
            messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
          }
        }, 100);
      };

      // Watch for route changes
      watch(
        () => route.params.id,
        (newId) => {
          if (newId) {
            loadConversation(newId);
          } else {
            currentConversation.value = null;
          }
        },
        { immediate: true }
      );

      return {
        currentConversation,
        isLoading,
        messagesContainer,
        handleSendMessage,
        currentUserId
      };
    }
  }
  </script>
  
  <style scoped>
  .chat-container {
    display: flex;
    height: 100vh;
    width: 100%;
    background-color: #ffffff;
  }
  
  .chat-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    height: 100%;
    background-color: #ffffff;
  }
  
  .chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    background-color: #f9f9f9;
  }
  
  .empty-chat {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 20px;
  }
  
  .empty-chat-content {
    text-align: center;
    max-width: 600px;
    padding: 40px;
    background-color: white;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  }
  
  .empty-chat-content h2 {
    font-size: 24px;
    color: #202123;
    margin-bottom: 16px;
  }
  
  .empty-chat-content p {
    color: #666;
    margin-bottom: 32px;
    font-size: 16px;
  }
  
  .empty-chat-features {
    display: flex;
    justify-content: center;
    gap: 32px;
    margin-top: 32px;
  }
  
  .feature {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }
  
  .feature-icon {
    font-size: 24px;
  }
  
  .feature span:last-child {
    color: #666;
    font-size: 14px;
  }
  </style>