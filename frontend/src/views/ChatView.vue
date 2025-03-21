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
        
        <ChatInput 
          @send="handleSendMessage" 
          :is-loading="isLoading"
          :conversation-id="currentConversation?.id"
        />
      </div>
    </div>
  </template>
  
  <script>
  import { ref, onMounted, watch, computed } from 'vue';
  import { useRoute } from 'vue-router';
  import { useStore } from 'vuex';
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
      const isLoading = ref(false);
      const messagesContainer = ref(null);

      const currentUserId = computed(() => String(store.state.auth.user?.id));
      const currentConversation = computed(() => store.state.chat.currentConversation);

      const handleSendMessage = async ({ content, isImageGeneration, isWebSearch }) => {
        if (!content.trim() || isLoading.value) return;
        
        let temporaryMessageId = null;
        
        try {
          isLoading.value = true;
          
          // If no conversation exists, create one
          if (!currentConversation.value) {
            try {
              const newConversation = await store.dispatch('chat/createConversation', 'New Chat');
              // Wait for the state to be updated
              await new Promise(resolve => setTimeout(resolve, 100));
              
              // If still no conversation after waiting, throw error
              if (!currentConversation.value) {
                console.error('Failed to create conversation: State was not updated');
                throw new Error('Failed to create conversation. Please try again.');
              }
            } catch (error) {
              console.error('Error creating conversation:', error);
              throw new Error('Failed to create conversation. Please try again.');
            }
          }

          // Safety check - ensure we have a valid conversation
          if (!currentConversation.value || !currentConversation.value.id) {
            throw new Error('Failed to create or load conversation');
          }

          // Create user message
          const userMessage = {
            id: Date.now(), // Temporary ID for frontend display
            content: content,
            role: 'user',
            conversation_id: currentConversation.value.id,
            created_at: new Date().toISOString()
          };
          temporaryMessageId = userMessage.id;

          // Add user message immediately
          await store.commit('chat/ADD_MESSAGE', { 
            conversationId: currentConversation.value.id, 
            message: userMessage 
          });
          scrollToBottom();

          // Send the message and get response
          const response = await store.dispatch('chat/sendMessage', {
            conversationId: currentConversation.value.id,
            content: content,
            isImageGeneration: isImageGeneration,
            isWebSearch: isWebSearch
          });

          // Update conversation title if it's the first message
          if (currentConversation.value.messages.length <= 2) {
            const newTitle = content.length > 30 
              ? content.substring(0, 30) + '...' 
              : content;
            await store.dispatch('chat/updateConversationTitle', {
              conversationId: currentConversation.value.id,
              title: newTitle
            });
          }

          // If this is an image response, display it properly
          if (response.content.startsWith('<image>') && response.content.endsWith('</image>')) {
            const base64Image = response.content.replace('<image>', '').replace('</image>', '');
            response.content = `<img src="data:image/png;base64,${base64Image}" alt="Generated image" class="generated-image" />`;
          }

          // Add assistant message
          await store.commit('chat/ADD_MESSAGE', {
            conversationId: currentConversation.value.id,
            message: response
          });
          scrollToBottom();

        } catch (error) {
          console.error('Error sending message:', error);
          
          if (temporaryMessageId) {
            // Remove the temporary message
            await store.commit('chat/REMOVE_MESSAGE', {
              conversationId: currentConversation.value.id,
              messageId: temporaryMessageId
            });
          }
          
          // Add error message
          const errorMessage = {
            id: Date.now(),
            content: error.message || 'Failed to get response. Please try again.',
            role: 'error',
            conversation_id: currentConversation.value?.id,
            created_at: new Date().toISOString()
          };
          await store.commit('chat/ADD_MESSAGE', {
            conversationId: currentConversation.value.id,
            message: errorMessage
          });
          scrollToBottom();
        } finally {
          isLoading.value = false;
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
        async (newId) => {
          if (newId) {
            await store.dispatch('chat/loadConversation', newId);
          } else {
            store.commit('chat/SET_CURRENT_CONVERSATION', null);
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