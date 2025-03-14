<template>
  <div
    class="conversation-item group relative flex items-center mb-2 text-sm font-medium rounded-lg cursor-pointer border border-black"
    :class="{
      'active': isActive,
      'text-gray-600': !isActive
    }"
    @click="$emit('select', conversation.id)"
  >
    <div class="conversation-content flex w-full items-center justify-between">
      <div class="conversation-title truncate">{{ conversation.title }}</div>
      
      <div class="menu-container">
        <button
          @click.stop="isMenuOpen = !isMenuOpen; updateDropdownPosition($event)"
          class="menu-button p-1.5 rounded-full hover:bg-gray-200 text-gray-500 text-lg leading-none"
        >
          ⠇
        </button>
      </div>
    </div>

    <!-- Dropdown Content -->
    <div
      v-if="isMenuOpen"
      class="fixed z-50"
      :style="{
        top: dropdownPosition.top + 'px',
        left: dropdownPosition.left + 'px'
      }"
    >
      <div class="bg-white rounded-lg shadow-lg border border-gray-200 w-[160px]">
        <div class="py-1" role="menu">
          <button
            class="w-full px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 text-right"
            @click.stop="handleRename"
          >
            Rename
          </button>
          <button
            class="w-full px-3 py-2 text-sm text-red-600 hover:bg-gray-50 text-right"
            @click.stop="$emit('delete', conversation.id)"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue';
import { useStore } from 'vuex';

export default {
  name: 'ConversationItem',
  props: {
    conversation: {
      type: Object,
      required: true
    },
    isActive: {
      type: Boolean,
      default: false
    }
  },
  emits: ['select', 'rename', 'delete'],
  setup(props) {
    const store = useStore();
    const isMenuOpen = ref(false);
    const dropdownPosition = ref({ top: 0, left: 0 });

    const updateDropdownPosition = (event) => {
      const button = event.target;
      const rect = button.getBoundingClientRect();
      dropdownPosition.value = {
        top: rect.bottom + 4,
        left: rect.right - 160 // Width of dropdown
      };
    };

    const handleRename = async () => {
      const newTitle = prompt('Enter new title:', props.conversation.title);
      if (newTitle && newTitle !== props.conversation.title) {
        try {
          await store.dispatch('chat/updateConversationTitle', {
            conversationId: props.conversation.id,
            title: newTitle
          });
          isMenuOpen.value = false;
        } catch (error) {
          console.error('Failed to rename conversation:', error);
          alert('Failed to rename conversation. Please try again.');
        }
      }
    };

    // Close menu when clicking outside
    const handleClickOutside = (event) => {
      if (isMenuOpen.value) {
        isMenuOpen.value = false;
      }
    };

    // Add and remove event listener
    onMounted(() => {
      document.addEventListener('click', handleClickOutside);
    });

    onUnmounted(() => {
      document.removeEventListener('click', handleClickOutside);
    });

    return {
      isMenuOpen,
      dropdownPosition,
      updateDropdownPosition,
      handleRename
    };
  }
};
</script>

<style scoped>
.conversation-item {
  transition: all 0.2s ease;
  border: 1px solid black !important;
  margin-bottom: 0.5rem !important;
  border-radius: 0.5rem !important;
  padding: 1rem !important;
}

.conversation-item:hover {
  background-color: #e9ebea !important;
  border-color: #e9ebea !important;
  color: rgb(7, 7, 7) !important;
}

.conversation-item.active {
  background-color: #d7d9d8 !important;
  border-color: #d7d9d8 !important;
  color: rgb(3, 3, 3) !important;
}

.conversation-content {
  display: flex !important;
  justify-content: space-between !important;
  align-items: center !important;
  width: 100% !important;
  gap: 1rem !important;
}

.conversation-title {
  padding: 0 0.5rem !important;
  flex: 1 !important;
}

.menu-container {
  display: flex !important;
  align-items: center !important;
  margin-left: auto !important;
}

.menu-button {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}
</style> 