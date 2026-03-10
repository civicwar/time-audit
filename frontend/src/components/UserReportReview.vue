<template>
  <v-card elevation="2" class="pa-4">
    <div class="d-flex align-center justify-space-between mb-4">
      <h2 class="text-h6">User Report Review</h2>
      <v-btn color="primary" variant="text" href="/in">Back to Workspace</v-btn>
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
        <v-btn
          color="primary"
          variant="outlined"
          :disabled="!canDownloadSelectedReport"
          @click="downloadSelectedReport"
        >
          {{ downloadSelectedButtonText }}
        </v-btn>
        <v-btn
          color="primary"
          variant="outlined"
          :disabled="!canDownloadAllReportsZip"
          @click="downloadAllReportsZip"
        >
          Download all reports.zip
        </v-btn>
        <div class="text-body-2">Total Entries: {{ filteredRows.length }}</div>
      </div>
      <v-expansion-panels v-if="groupByDate" multiple>
        <v-expansion-panel
          v-for="group in dateGroups"
          :key="group.date"
        >
          <v-expansion-panel-title>
            {{ group.date }} ({{ group.items.length }})
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-data-table
              :headers="groupedHeaders"
              :items="group.items"
              density="comfortable"
              item-value="id"
              :sort-by="[{ key: 'user', order: 'asc' }, { key: 'description', order: 'asc' }]"
            />
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
      <v-data-table
        v-else
        :headers="headers"
        :items="filteredRows"
        density="comfortable"
        item-value="id"
        :sort-by="[{ key: 'date', order: 'asc' }, { key: 'user', order: 'asc' }]"
      />
    </div>
  </v-card>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import api from '../services/api'

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
const reportFiles = ref([])
const selectedUser = ref('All users')
const groupByDate = ref(true)

const headers = [
  { title: 'User', key: 'user' },
  { title: 'Date', key: 'date' },
  { title: 'Task', key: 'description' },
  { title: 'Duration (h)', key: 'duration' },
  { title: 'Duration', key: 'duration_hm' },
]

const groupedHeaders = [
  { title: 'User', key: 'user' },
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

const selectedReportFile = computed(() => {
  if (selectedUser.value === 'All users') return null
  return reportFiles.value.find((rf) => rf.user === selectedUser.value) || null
})

const canDownloadSelectedReport = computed(() => Boolean(selectedReportFile.value?.relative_path))

const canDownloadAllReportsZip = computed(() => Boolean(runDir.value && reportFiles.value.length))

const downloadSelectedButtonText = computed(() => {
  if (selectedUser.value === 'All users') return 'Select a user to download report.json'
  return `Download ${selectedUser.value} report.json`
})

const dateGroups = computed(() => {
  const grouped = filteredRows.value.reduce((acc, row) => {
    if (!acc[row.date]) acc[row.date] = []
    acc[row.date].push(row)
    return acc
  }, {})

  return Object.keys(grouped)
    .sort((a, b) => String(a).localeCompare(String(b)))
    .map((date) => ({
      date,
      items: grouped[date],
    }))
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
  reportFiles.value = []
  try {
    const { data: runData } = await api.get(`/api/in/reports/${runDir.value}`)
    const files = runData?.report_files || []
    reportFiles.value = files
    if (!files.length) {
      rows.value = []
      return
    }

    const reportResponses = await Promise.all(
      files.map(async (rf) => {
        const response = await api.get(`/api/in/reports/files/${rf.relative_path}`)
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

const downloadSelectedReport = async () => {
  if (!selectedReportFile.value) return
  try {
    const response = await api.get(`/api/in/reports/files/${selectedReportFile.value.relative_path}`, {
      responseType: 'blob',
    })
    const blobUrl = window.URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = `${selectedUser.value.replace(/\s+/g, '_').toLowerCase()}_report.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(blobUrl)
  } catch (e) {
    error.value = e.response?.data?.detail || 'Could not download selected report.'
  }
}

const downloadAllReportsZip = async () => {
  if (!canDownloadAllReportsZip.value) return
  try {
    const response = await api.get(`/api/in/reports/${runDir.value}/zip`, {
      responseType: 'blob',
    })
    const blobUrl = window.URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = `${runDir.value}_reports.zip`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(blobUrl)
  } catch (e) {
    error.value = e.response?.data?.detail || 'Could not download reports zip.'
  }
}

onMounted(loadReport)
watch(() => props.reportPath, loadReport)
</script>
