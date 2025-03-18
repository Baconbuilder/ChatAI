// ChatMessage.vue
<template>
  <div class="message" :class="{
    'user': message.role === 'user',
    'assistant': message.role === 'assistant',
    'error': message.type === 'error'
  }">
    <div class="message-content">
      <template v-if="isImageContent">
        <div class="text-content">{{ textContent }}</div>
        <img :src="fullImageUrl" alt="Generated image" class="generated-image" @click="handleImageClick" />
        <div class="text-content">{{ followUpText }}</div>
      </template>
      <template v-else>
        {{ message.content }}
      </template>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue';

export default {
  name: 'ChatMessage',
  props: {
    message: {
      type: Object,
      required: true
    },
    currentUserId: {
      type: String,
      required: true
    }
  },
  setup(props) {
    const isUser = computed(() => props.message.userId === props.currentUserId);
    
    const isImageContent = computed(() => {
      const content = props.message.content;
      return content && (
        content.includes('<img') || 
        content.includes('/static/images/')
      );
    });

    const imageUrl = computed(() => {
      if (!isImageContent.value) return '';
      const content = props.message.content;
      // Extract URL from img tag if present
      const imgMatch = content.match(/src="([^"]+)"/);
      if (imgMatch) return imgMatch[1];
      // If no img tag, return the content directly
      return content;
    });

    const fullImageUrl = computed(() => {
      if (!imageUrl.value) return '';
      // If the URL already starts with http, return it as is
      if (imageUrl.value.startsWith('http')) return imageUrl.value;
      // Otherwise, prepend the API URL
      return `${import.meta.env.VITE_API_URL.replace('/api', '')}${imageUrl.value}`;
    });

    const textContent = computed(() => {
      if (!isImageContent.value) return '';
      const content = props.message.content;
      // Extract text before the image tag
      const beforeImg = content.split('<img')[0].trim();
      return beforeImg;
    });

    const followUpText = computed(() => {
      if (!isImageContent.value) return '';
      const content = props.message.content;
      // Extract text after the image tag, handling both self-closing and regular closing tags
      const afterImg = content.split('/>')[1]?.trim() || '';
      return afterImg;
    });

    const handleImageClick = () => {
      if (fullImageUrl.value) {
        window.open(fullImageUrl.value, '_blank');
      }
    };

    return {
      isUser,
      isImageContent,
      imageUrl,
      fullImageUrl,
      textContent,
      followUpText,
      handleImageClick
    };
  }
};
</script>

<style scoped>
.message {
  display: flex;
  padding: 0.75rem;
  margin: 0.5rem 0;
  border-radius: 12px;
  max-width: 70%;
  position: relative;
  color: #333;
}

.message.user {
  background-color: #f5f5f5;
  margin-left: auto;
  margin-right: 0;
  border: 1px solid #333;
}

.message.assistant {
  background-color: #ffffff;
  border: 1px solid #e0e0e0;
  margin-right: auto;
  margin-left: 0;
}

.message.error {
  margin: 1rem auto;
  background-color: #ffebee;
  color: #d32f2f;
  border: 1px solid #ffcdd2;
  font-size: 0.9em;
  text-align: center;
  max-width: 60%;
}

.message-avatar {
  width: 30px;
  height: 30px;
  margin-right: 15px;
  flex-shrink: 0;
}

.message-avatar img {
  width: 100%;
  height: 100%;
  border-radius: 3px;
  object-fit: cover;
}

.message-content {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.5;
}

.text-content {
  margin: 0.5rem 0;
  line-height: 1.6;
}

.generated-image {
  max-width: 100%;
  max-height: 400px;
  border-radius: 8px;
  margin: 8px 0;
  cursor: pointer;
  transition: transform 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.generated-image:hover {
  transform: scale(1.02);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.message-content pre {
  background-color: #f6f8fa;
  padding: 10px;
  border-radius: 5px;
  overflow: auto;
  margin: 0.5rem 0;
}

.message-content code {
  font-family: monospace;
  background-color: rgba(0, 0, 0, 0.05);
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-size: 0.9em;
}

/* Add space between consecutive messages */
.message + .message {
  margin-top: 0.75rem;
}
</style>

