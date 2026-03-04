<template>
  <v-card elevation="2" class="pa-4">
    <div class="d-flex align-center justify-space-between mb-4">
      <h2 class="text-h6">User Report Review: {{ userLabel }}</h2>
      <v-btn color="primary" variant="text" href="#/">Back to Upload</v-btn>
    </div>

    <v-alert
      v-if="error"
      type="error"
      variant="tonal"
      class="mb-4"
      :text="error"
    />

    <v-progress-linear
      v-if="loading"
      indeterminate
      color="primary"
      class="mb-4"
    />

    <div v-if="!loading && !error">
      <div class="text-body-2 mb-3">Total Entries: {{ rows.length }}</div>
      <v-data-table
        :headers="headers"
        :items="rows"
        density="comfortable"
        item-value="id"
        :sort-by="[{ key: 'date', order: 'asc' }]"
      />
    </div>
  </v-card>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'

const props = defineProps({
  reportPath: {
    type: String,
    required: true,
  },
  user: {
    type: String,
    default: '',
  },
})

const loading = ref(false)
const error = ref('')
const rows = ref([])

const headers = [
  { title: 'Date', key: 'date' },
  { title: 'Task', key: 'description' },
  { title: 'Duration (h)', key: 'duration' },
  { title: 'Duration', key: 'duration_hm' },
]

const userLabel = computed(() => props.user || 'Unknown User')

const loadReport = async () => {
  loading.value = true
  error.value = ''
  rows.value = []
  try {
    const { data } = await axios.get(`/reports/${props.reportPath}`)
    const flatRows = []
    Object.entries(data || {}).forEach(([date, tasks]) => {
      ;(tasks || []).forEach((task, index) => {
        flatRows.push({
          id: `${date}-${index}-${task.description}`,
          date,
          description: task.description,
          duration: task.duration,
          duration_hm: task.duration_hm,
        })
      })
    })
    rows.value = flatRows
  } catch (e) {
    error.value = e.response?.data?.detail || 'Could not load user report.'
  } finally {
    loading.value = false
  }
}

onMounted(loadReport)
</script>
