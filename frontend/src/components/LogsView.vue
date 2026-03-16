<template>
  <v-card elevation="2" class="pa-4">
    <div class="d-flex align-center justify-space-between mb-4 flex-wrap ga-3">
      <div>
        <h2 class="text-h6">Application Logs</h2>
        <div class="text-body-2 text-medium-emphasis">Admin-only access</div>
      </div>
      <div class="d-flex align-center ga-2 flex-wrap">
        <v-select
          v-model="lines"
          :items="lineOptions"
          label="Lines"
          density="compact"
          hide-details
          style="max-width: 120px"
        />
        <v-btn variant="text" href="/in">Back to Workspace</v-btn>
        <v-btn color="primary" :loading="loading" @click="loadLogs">Refresh</v-btn>
      </div>
    </div>

    <v-alert
      v-if="!isAdmin"
      type="error"
      variant="tonal"
      text="Only admins can access application logs."
    />

    <template v-else>
      <v-alert v-if="error" type="error" variant="tonal" class="mb-4" :text="error" />
      <v-alert
        v-else-if="!logData.available"
        type="info"
        variant="tonal"
        class="mb-4"
        text="No application log file is available yet. Trigger a request or wait for the next backend restart."
      />

      <v-card variant="outlined" class="pa-4 mb-4">
        <div class="text-body-2"><strong>Path:</strong> {{ logData.path || 'Unavailable' }}</div>
        <div class="text-body-2"><strong>Last Updated:</strong> {{ formattedUpdatedAt }}</div>
        <div class="text-body-2"><strong>Size:</strong> {{ formattedSize }}</div>
        <div class="text-body-2"><strong>Loaded Lines:</strong> {{ logData.line_count }}</div>
      </v-card>

      <v-sheet
        rounded
        border
        color="surface-variant"
        class="log-output pa-4"
      >
        <pre>{{ logData.content || 'No log lines available.' }}</pre>
      </v-sheet>
    </template>
  </v-card>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import api, { getStoredSession } from '../services/api'

const authSession = ref(getStoredSession())
const isAdmin = computed(() => authSession.value?.user?.role === 'Admin')
const loading = ref(false)
const error = ref('')
const lines = ref(200)
const lineOptions = [100, 200, 500, 1000, 2000]
const logData = ref({
  available: false,
  path: '',
  content: '',
  line_count: 0,
  updated_at: null,
  size_bytes: 0,
})

const formattedUpdatedAt = computed(() => {
  if (!logData.value.updated_at) {
    return 'Unavailable'
  }

  const date = new Date(logData.value.updated_at)
  if (Number.isNaN(date.getTime())) {
    return logData.value.updated_at
  }
  return date.toLocaleString()
})

const formattedSize = computed(() => {
  const size = Number(logData.value.size_bytes || 0)
  if (!size) {
    return '0 B'
  }

  if (size < 1024) {
    return `${size} B`
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`
  }
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
})

const loadLogs = async () => {
  if (!isAdmin.value) {
    return
  }

  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get('/api/in/logs', {
      params: { lines: lines.value },
    })
    logData.value = data
  } catch (requestError) {
    error.value = requestError.response?.data?.detail || 'Could not load application logs.'
  } finally {
    loading.value = false
  }
}

watch(lines, () => {
  if (isAdmin.value) {
    loadLogs()
  }
})

onMounted(loadLogs)
</script>

<style scoped>
.log-output {
  max-height: 70vh;
  overflow: auto;
}

.log-output pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  font-size: 0.875rem;
  line-height: 1.5;
}
</style>