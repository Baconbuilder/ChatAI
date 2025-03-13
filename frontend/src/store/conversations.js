// store/conversations.js
// Dummy data for initial development
const dummyConversations = [
    {
      id: '1',
      title: 'Help with Vue.js Project',
      createdAt: '2025-03-01T12:00:00Z',
      messages: [
        {
          id: '101',
          role: 'user',
          content: 'How do I set up a new Vue.js project?',
          timestamp: '2025-03-01T12:00:00Z'
        },
        {
          id: '102',
          role: 'assistant',
          content: 'To set up a new Vue.js project, you can use Vue CLI. First, install it globally with npm:\n\n```\nnpm install -g @vue/cli\n```\n\nThen create a new project with:\n\n```\nvue create my-project\n```\n\nFollow the prompts to select the features you need.',
          timestamp: '2025-03-01T12:01:00Z'
        }
      ]
    },
    {
      id: '2',
      title: 'Python API Implementation',
      createdAt: '2025-03-03T14:30:00Z',
      messages: [
        {
          id: '201',
          role: 'user',
          content: 'What\'s the best framework for building a REST API in Python?',
          timestamp: '2025-03-03T14:30:00Z'
        },
        {
          id: '202',
          role: 'assistant',
          content: 'For Python REST APIs, Flask and FastAPI are excellent choices. If you need something lightweight and flexible, Flask is great. For high performance and automatic API documentation, FastAPI is the best option. Django REST Framework is another robust choice if you\'re working with Django.',
          timestamp: '2025-03-03T14:31:00Z'
        }
      ]
    }
  ];
  
  export default {
    state: {
      list: [],
      isLoading: false,
      error: null
    },
    mutations: {
      SET_CONVERSATIONS(state, conversations) {
        state.list = conversations;
      },
      ADD_CONVERSATION(state, conversation) {
        state.list.push(conversation);
      },
      ADD_MESSAGE(state, { conversationId, message }) {
        const conversation = state.list.find(c => c.id === conversationId);
        if (conversation) {
          conversation.messages.push(message);
        }
      },
      UPDATE_CONVERSATION_TITLE(state, { conversationId, title }) {
        const conversation = state.list.find(c => c.id === conversationId);
        if (conversation) {
          conversation.title = title;
        }
      },
      SET_LOADING(state, isLoading) {
        state.isLoading = isLoading;
      },
      SET_ERROR(state, error) {
        state.error = error;
      }
    },
    actions: {
      fetchConversations({ commit }) {
        commit('SET_LOADING', true);
        
        // In a real app, this would be an API call
        // For now, we'll use dummy data
        setTimeout(() => {
          commit('SET_CONVERSATIONS', dummyConversations);
          commit('SET_LOADING', false);
        }, 500);
      },
      addConversation({ commit }, conversation) {
        commit('ADD_CONVERSATION', conversation);
        
        // In a real app, save to API/database
      },
      addMessageToConversation({ commit }, { conversationId, message }) {
        commit('ADD_MESSAGE', { conversationId, message });
        
        // In a real app, save to API/database
      },
      updateConversationTitle({ commit }, { conversationId, title }) {
        commit('UPDATE_CONVERSATION_TITLE', { conversationId, title });
        
        // In a real app, save to API/database
      }
    }
  };