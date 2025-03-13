<template>
    <div class="chat-container">
      <Sidebar />
      
      <div class="chat-main">
        <Header :title="currentConversation?.title || 'New Conversation'" />
        
        <div class="chat-messages" ref="messagesContainer">
          <div v-if="!currentConversation || !currentConversation.messages.length" class="empty-chat">
            <div class="empty-chat-content">
              <h2>Welcome to ChatAI</h2>
              <p>Start a new conversation or select an existing one from the sidebar.</p>
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
            v-for="(message, index) in currentConversation?.messages || []" 
            :key="index" 
            :message="message" 
          />
        </div>
        
        <ChatInput @send-message="sendMessage" :is-loading="isLoading" />
      </div>
    </div>
  </template>
  
  <script>
  import { ref, onMounted, watch } from 'vue';
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

      const loadConversation = async (id) => {
        if (!id) return;
        try {
          const response = await conversationService.getConversation(id);
          currentConversation.value = response;
          store.commit('setCurrentConversation', response);
        } catch (error) {
          console.error('Failed to load conversation:', error);
        }
      };

      const createNewConversation = async () => {
        try {
          const newConversation = await conversationService.createConversation('New Chat');
          currentConversation.value = newConversation;
          return newConversation;
        } catch (error) {
          console.error('Failed to create new conversation:', error);
          throw error;
        }
      };

      const sendMessage = async (content) => {
        if (!content.trim()) return;
        
        isLoading.value = true;
        
        try {
          // Create new conversation if none exists
          if (!currentConversation.value) {
            await createNewConversation();
          }
          
          // Send the message
          const message = await conversationService.sendMessage(
            currentConversation.value.id,
            content
          );
          
          // Add the message to the current conversation
          if (!currentConversation.value.messages) {
            currentConversation.value.messages = [];
          }
          currentConversation.value.messages.push(message);
          
          // Update the conversation title if it's the first message
          if (currentConversation.value.messages.length === 1) {
            const newTitle = content.length > 30 
              ? content.substring(0, 30) + '...' 
              : content;
            await conversationService.updateConversationTitle(
              currentConversation.value.id,
              newTitle
            );
            currentConversation.value.title = newTitle;
          }
          
          scrollToBottom();
        } catch (error) {
          console.error('Error sending message:', error);
        } finally {
          isLoading.value = false;
        }
      };

      const scrollToBottom = () => {
        if (messagesContainer.value) {
          messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
        }
      };

      // Watch for route changes
      watch(
        () => route.params.id,
        (newId) => {
          if (newId) {
            loadConversation(newId);
          }
        },
        { immediate: true }
      );

      // Watch for message changes
      watch(
        () => currentConversation.value?.messages,
        () => {
          scrollToBottom();
        },
        { deep: true }
      );

      onMounted(() => {
        if (route.params.id) {
          loadConversation(route.params.id);
        }
      });

      return {
        currentConversation,
        isLoading,
        messagesContainer,
        sendMessage
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