<template>
  <div
    class="group relative flex items-center px-2 py-2 text-sm font-medium rounded-md cursor-pointer"
    :class="{
      'bg-gray-100 text-gray-900': isActive,
      'text-gray-600 hover:bg-gray-50 hover:text-gray-900': !isActive
    }"
    @click="$emit('select', conversation.id)"
  >
    <div class="flex-1 min-w-0">
      <div class="truncate">{{ conversation.title }}</div>
      <div class="text-xs text-gray-500">
        {{ formatDate(conversation.updated_at) }}
      </div>
    </div>
    <button
      class="ml-2 opacity-0 group-hover:opacity-100 p-1 rounded-full hover:bg-gray-200"
      @click.stop="$emit('delete', conversation.id)"
    >
      <svg
        class="h-4 w-4 text-gray-500"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 20 20"
        fill="currentColor"
      >
        <path
          fill-rule="evenodd"
          d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
          clip-rule="evenodd"
        />
      </svg>
    </button>
  </div>
</template>

<script>
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
  emits: ['select', 'delete'],
  setup() {
    const formatDate = (dateString) => {
      const date = new Date(dateString);
      const now = new Date();
      const diff = now - date;
      
      // If less than 24 hours ago
      if (diff < 24 * 60 * 60 * 1000) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      }
      
      // If less than 7 days ago
      if (diff < 7 * 24 * 60 * 60 * 1000) {
        return date.toLocaleDateString([], { weekday: 'short' });
      }
      
      // Otherwise, show the date
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    };

    return {
      formatDate
    };
  }
};
</script> 