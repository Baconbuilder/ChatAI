// ChatInput.vue
<template>
  <div class="chat-input-container">
    <div class="relative flex flex-col gap-2">
      <!-- File upload section -->
      <div class="flex items-center gap-2">
        <input
          type="file"
          ref="fileInput"
          accept=".pdf"
          class="hidden"
          @change="handleFileUpload"
          multiple
        />
        <button
          type="button"
          class="upload-button"
          @click="$refs.fileInput.click()"
          :disabled="isLoading"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Upload PDF
        </button>
      </div>
      
      <!-- Display uploaded files -->
      <div v-if="uploadedFiles.length > 0" class="uploaded-files">
        <div class="text-sm text-gray-500 mb-1">Uploaded files:</div>
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

      <!-- Message input section -->
      <div class="input-wrapper">
        <textarea
          ref="textarea"
          v-model="message"
          rows="3"
          class="message-input"
          placeholder="Type your message..."
          @keydown.enter.prevent="handleEnter"
        ></textarea>
        <button
          type="button"
          class="send-button"
          :disabled="!message.trim() || isLoading"
          @click="sendMessage"
        >
          <span v-if="isLoading">Sending...</span>
          <span v-else>Send</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue';
import { uploadService } from '@/services/uploadService';

export default {
  name: 'ChatInput',
  props: {
    isLoading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['send', 'fileUploaded'],
  setup(props, { emit }) {
    const message = ref('');
    const textarea = ref(null);
    const uploadedFiles = ref([]);
    const uploadStatus = ref(null);

    const handleEnter = (event) => {
      if (event.shiftKey) return;
      sendMessage();
    };

    const handleFileUpload = async (event) => {
      const files = Array.from(event.target.files);
      if (!files.length) return;

      try {
        uploadStatus.value = { type: 'info', message: 'Uploading files...' };
        
        for (const file of files) {
          const formData = new FormData();
          formData.append('file', file);
          
          const response = await uploadService.uploadPDF(formData);
          uploadedFiles.value.push({
            name: file.name,
            id: response.id
          });
          
          emit('fileUploaded', response);
        }
        
        uploadStatus.value = { type: 'success', message: 'Files uploaded successfully!' };
        event.target.value = ''; // Reset file input
        
        // Add a message about the uploaded files
        // const fileNames = files.map(f => f.name).join(', ');
        // message.value = `I've uploaded the following PDF(s): ${fileNames}. Please help me understand their content.`;
        
      } catch (error) {
        console.error('Error uploading files:', error);
        uploadStatus.value = { type: 'error', message: 'Error uploading files. Please try again.' };
      }
    };

    const removeFile = (file) => {
      uploadedFiles.value = uploadedFiles.value.filter(f => f.id !== file.id);
    };

    const sendMessage = async () => {
      if (!message.value.trim() || props.isLoading) return;

      emit('send', message.value.trim());
      message.value = '';
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
      handleEnter,
      sendMessage,
      handleFileUpload,
      removeFile
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
  background-color: #0d8a6c;
}

.send-button:disabled {
  background-color: #e5e5e5;
  cursor: not-allowed;
}

.upload-button {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  background-color: white;
  border: 1px solid #e5e5e5;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #666;
  transition: all 0.2s;
}

.upload-button:hover:not(:disabled) {
  background-color: #f5f5f5;
  border-color: #d5d5d5;
}

.uploaded-files {
  margin-top: 4px;
}

.file-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background-color: #f5f5f5;
  border-radius: 4px;
  font-size: 12px;
}

.file-tag button {
  padding: 0 4px;
  font-size: 16px;
  line-height: 1;
}
</style>