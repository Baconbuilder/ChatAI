// ChatInput.vue
<template>
  <div class="border-t border-gray-200 px-4 pt-4 sm:px-6">
    <div class="relative flex flex-col gap-2">
      <div class="flex items-center gap-2 mb-2">
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
          class="inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          @click="$refs.fileInput.click()"
          :disabled="isLoading"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Upload PDF
        </button>
        <div v-if="uploadStatus" class="text-sm" :class="uploadStatus.type === 'error' ? 'text-red-600' : 'text-green-600'">
          {{ uploadStatus.message }}
        </div>
      </div>
      
      <!-- Display uploaded files -->
      <div v-if="uploadedFiles.length > 0" class="mb-2">
        <div class="text-sm text-gray-500 mb-1">Uploaded files:</div>
        <div class="flex flex-wrap gap-2">
          <div
            v-for="file in uploadedFiles"
            :key="file.name"
            class="flex items-center gap-1 bg-gray-100 rounded-md px-2 py-1 text-sm"
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

      <textarea
        ref="textarea"
        v-model="message"
        rows="3"
        class="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
        placeholder="Type your message..."
        @keydown.enter.prevent="handleEnter"
      ></textarea>
      <div class="absolute bottom-0 right-0 flex items-center pr-3">
        <button
          type="button"
          class="inline-flex items-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
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
        const fileNames = files.map(f => f.name).join(', ');
        message.value = `I've uploaded the following PDF(s): ${fileNames}. Please help me understand their content.`;
        
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
  padding: 10px 20px;
  background-color: white;
  border-top: 1px solid #e5e5e5;
}

.input-wrapper {
  display: flex;
  position: relative;
}

textarea {
  flex: 1;
  height: 52px;
  max-height: 200px;
  padding: 15px;
  padding-right: 50px;
  border: 1px solid #e5e5e5;
  border-radius: 6px;
  resize: none;
  outline: none;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.5;
}

textarea:focus {
  border-color: #10a37f;
}

.send-button {
  position: absolute;
  right: 10px;
  bottom: 13px;
  background: none;
  border: none;
  color: #10a37f;
  cursor: pointer;
  font-size: 18px;
}

.send-button:disabled {
  color: #d9d9e3;
  cursor: not-allowed;
}

.input-footer {
  margin-top: 5px;
  font-size: 12px;
  color: #8e8ea0;
  text-align: right;
}
</style>