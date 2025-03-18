// ChatInput.vue
<template>
  <div class="chat-input-container">
    <div class="relative flex flex-col gap-2">
      <!-- File upload, image generation, and web search section -->
      <div class="flex items-center gap-4">
        <input
          type="file"
          ref="fileInput"
          accept=".pdf"
          class="hidden absolute"
          style="opacity: 0; width: 0; height: 0;"
          @change="handleFileUpload"
          multiple
        />
        <button
          type="button"
          class="upload-button"
          @click="$refs.fileInput.click()"
          :disabled="isLoading || isUploading"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Upload PDF
        </button>

        <button
          type="button"
          class="upload-button"
          :class="{ 'active': isImageMode }"
          @click="toggleImageMode"
          :disabled="isLoading || isUploading"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          {{ isImageMode ? 'Image Mode' : 'Generate Image' }}
        </button>
        
        <button
          type="button"
          class="upload-button"
          :class="{ 'active': isWebSearchMode }"
          @click="toggleWebSearchMode"
          :disabled="isLoading || isUploading"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          {{ isWebSearchMode ? 'Web Search Mode' : 'Web Search' }}
        </button>
        
        <!-- Display uploaded files inline -->
        <div v-if="uploadedFiles.length > 0" class="flex items-center gap-2">
          <div class="flex flex-wrap gap-2">
            <div
              v-for="file in uploadedFiles"
              :key="file.name"
              class="file-tag"
            >
              <span>{{ file.name }}</span>
              <button
                @click="removeFile(file)"
                class="text-gray-500 hover:text-red-500"
              >
                ×
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Message input section -->
      <div class="input-wrapper">
        <textarea
          ref="textarea"
          v-model="message"
          rows="3"
          class="message-input"
          :placeholder="getInputPlaceholder()"
          @keydown.enter.prevent="handleEnter"
        ></textarea>
        <button
          type="button"
          class="send-button"
          :disabled="!message.trim() || isLoading || isUploading"
          @click="sendMessage"
        >
          <span v-if="isLoading">{{ getButtonText(true) }}</span>
          <span v-else-if="isUploading">Uploading...</span>
          <span v-else>{{ getButtonText(false) }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue';
import { useStore } from 'vuex';
import { uploadService } from '@/services/uploadService';

export default {
  name: 'ChatInput',
  props: {
    isLoading: {
      type: Boolean,
      default: false
    },
    conversationId: {
      type: [String, Number],
      required: true,
      default: null
    }
  },
  emits: ['send', 'fileUploaded'],
  setup(props, { emit }) {
    const store = useStore();
    const message = ref('');
    const textarea = ref(null);
    const uploadedFiles = ref([]);
    const uploadStatus = ref(null);
    const isUploading = ref(false);
    const isImageMode = ref(false);
    const isWebSearchMode = ref(false);

    const toggleImageMode = () => {
      isImageMode.value = !isImageMode.value;
      if (isImageMode.value && isWebSearchMode.value) {
        isWebSearchMode.value = false;
      }
    };

    const toggleWebSearchMode = () => {
      isWebSearchMode.value = !isWebSearchMode.value;
      if (isWebSearchMode.value && isImageMode.value) {
        isImageMode.value = false;
      }
    };

    const getInputPlaceholder = () => {
      if (isImageMode.value) {
        return 'Describe the image you want to generate...';
      } else if (isWebSearchMode.value) {
        return 'Ask a question that requires up-to-date information...';
      } else {
        return 'Type your message...';
      }
    };

    const getButtonText = (isLoadingState) => {
      if (isLoadingState) {
        if (isImageMode.value) return 'Generating...';
        if (isWebSearchMode.value) return 'Searching...';
        return 'Sending...';
      } else {
        if (isImageMode.value) return 'Generate';
        if (isWebSearchMode.value) return 'Search';
        return 'Send';
      }
    };

    const handleEnter = (event) => {
      if (event.shiftKey) return;
      sendMessage();
    };

    const handleFileUpload = async (event) => {
      const files = Array.from(event.target.files);
      if (!files.length) return;

      try {
        // If no conversation exists, create one first
        let currentConversationId = props.conversationId;
        if (!currentConversationId) {
          const newConversation = await store.dispatch('chat/createConversation', 'New Chat');
          currentConversationId = newConversation.id;
        }

        isUploading.value = true;
        uploadStatus.value = { type: 'info', message: 'Uploading files...' };
        
        for (const file of files) {
          const formData = new FormData();
          formData.append('file', file);
          
          const response = await uploadService.uploadPDF(formData, currentConversationId);
          uploadedFiles.value.push({
            name: file.name,
            id: response.id
          });
          
          emit('fileUploaded', response);
        }
        
        uploadStatus.value = { type: 'success', message: 'Files uploaded successfully!' };
        event.target.value = ''; // Reset file input
        
      } catch (error) {
        console.error('Error uploading files:', error);
        uploadStatus.value = { type: 'error', message: 'Error uploading files. Please try again.' };
      } finally {
        isUploading.value = false;
      }
    };

    const removeFile = (file) => {
      uploadedFiles.value = uploadedFiles.value.filter(f => f.id !== file.id);
    };

    const sendMessage = async () => {
      if (!message.value.trim() || props.isLoading) return;

      const content = message.value.trim();
      emit('send', { 
        content, 
        isImageGeneration: isImageMode.value,
        isWebSearch: isWebSearchMode.value 
      });
      message.value = '';
      if (isImageMode.value) {
        isImageMode.value = false; // Turn off image mode after sending
      }
      if (isWebSearchMode.value) {
        isWebSearchMode.value = false; // Turn off web search mode after sending
      }
      await nextTick();
      textarea.value?.focus();
    };

    onMounted(() => {
      textarea.value?.focus();
    });

    return {
      message,
      textarea,
      uploadedFiles,
      uploadStatus,
      isUploading,
      isImageMode,
      isWebSearchMode,
      handleEnter,
      sendMessage,
      handleFileUpload,
      removeFile,
      toggleImageMode,
      toggleWebSearchMode,
      getInputPlaceholder,
      getButtonText
    };
  }
};
</script>

<style scoped>
.chat-input-container {
  padding: 8px 16px;
  background-color: white;
  border-top: 1px solid #e5e5e5;
  margin-top: auto;
}

.input-wrapper {
  display: flex;
  position: relative;
  margin-top: 8px;
}

.message-input {
  width: 100%;
  min-height: 44px;
  max-height: 200px;
  padding: 12px;
  padding-right: 100px;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  resize: none;
  outline: none;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.5;
  background-color: #fff;
}

.message-input:focus {
  border-color: #10a37f;
  box-shadow: 0 0 0 2px rgba(16, 163, 127, 0.1);
}

.send-button {
  position: absolute;
  right: 8px;
  bottom: 8px;
  padding: 6px 12px;
  background-color: #10a37f;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.send-button:hover:not(:disabled) {
  background-color: #0d8c6c;
}

.send-button:disabled {
  background-color: #e5e5e5;
  color: #a8a8a8;
  cursor: not-allowed;
}

.upload-button {
  display: flex;
  align-items: center;
  padding: 6px 10px;
  background-color: #f5f5f5;
  color: #333;
  border: 1px solid #e5e5e5;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-button:hover:not(:disabled) {
  background-color: #e5e5e5;
}

.upload-button:disabled {
  background-color: #f9f9f9;
  color: #c5c5c5;
  cursor: not-allowed;
}

.upload-button.active {
  background-color: #10a37f;
  color: white;
  border-color: #10a37f;
}

.file-tag {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  background-color: #e5f7f2;
  border: 1px solid #c5eae0;
  border-radius: 4px;
  font-size: 12px;
  color: #0d8c6c;
}

.file-tag button {
  margin-left: 4px;
  padding: 0 4px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
}
</style>