<template>
  <v-card elevation="2" class="pa-4">
    <div class="d-flex align-center justify-space-between mb-4">
      <h2 class="text-h6">User Report Review</h2>
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
      <div class="d-flex flex-wrap align-center ga-3 mb-3">
        <v-select
          v-model="selectedUser"
          :items="userOptions"
          label="User"
          density="comfortable"
          hide-details
          style="max-width: 320px"
        />
        <v-switch
          v-model="groupByDate"
          color="primary"
          hide-details
          label="Group by date"
        />
        <div class="text-body-2">Total Entries: {{ filteredRows.length }}</div>
      </div>
      <v-data-table
        :headers="headers"
        :items="filteredRows"
        density="comfortable"
        item-value="id"
        :sort-by="[{ key: 'date', order: 'asc' }]"
        :group-by="tableGroupBy"
      />
    </div>
  </v-card>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
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
const selectedUser = ref('All users')
const groupByDate = ref(true)

const headers = [
  { title: 'User', key: 'user' },
  { title: 'Date', key: 'date' },
  { title: 'Task', key: 'description' },
  { title: 'Duration (h)', key: 'duration' },
  { title: 'Duration', key: 'duration_hm' },
]

const runDir = computed(() => {
  const [dir] = (props.reportPath || '').split('/')
  return dir || ''
})

const userOptions = computed(() => {
  const users = Array.from(new Set(rows.value.map((r) => r.user))).sort()
  return ['All users', ...users]
})

const filteredRows = computed(() => {
  if (selectedUser.value === 'All users') return rows.value
  return rows.value.filter((r) => r.user === selectedUser.value)
})

const tableGroupBy = computed(() => {
  if (!groupByDate.value) return []
  return [{ key: 'date', order: 'asc' }]
})

const loadReport = async () => {
  if (!runDir.value) {
    error.value = 'Missing run directory.'
    rows.value = []
    return
  }

  loading.value = true
  error.value = ''
  rows.value = []
  try {
    const { data: runData } = await axios.get(`/api/reports/${runDir.value}`)
    const reportFiles = runData?.report_files || []
    if (!reportFiles.length) {
      rows.value = []
      return
    }

    const reportResponses = await Promise.all(
      reportFiles.map(async (rf) => {
        const response = await axios.get(`/reports/${rf.relative_path}`)
        return { user: rf.user, report: response.data }
      })
    )

    const flatRows = []
    reportResponses.forEach(({ user, report }) => {
      Object.entries(report || {}).forEach(([date, tasks]) => {
        ;(tasks || []).forEach((task, index) => {
          flatRows.push({
            id: `${user}-${date}-${index}-${task.description}`,
            user,
            date,
            description: task.description,
            duration: task.duration,
            duration_hm: task.duration_hm,
          })
        })
      })
    })

    rows.value = flatRows
    if (props.user && userOptions.value.includes(props.user)) {
      selectedUser.value = props.user
    } else {
      selectedUser.value = 'All users'
    }
  } catch (e) {
    error.value = e.response?.data?.detail || 'Could not load run reports.'
  } finally {
    loading.value = false
  }
}

onMounted(loadReport)
watch(() => props.reportPath, loadReport)
</script>
