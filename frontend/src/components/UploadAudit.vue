<template>
  <v-card elevation="2" class="pa-4">
    <div class="d-flex align-center justify-space-between mb-4">
      <div>
        <h2 class="text-h6">Audit Workspace</h2>
        <div class="text-body-2 text-medium-emphasis">Upload new Clockify exports and review past runs.</div>
      </div>
    </div>

    <v-form @submit.prevent="submit">
      <v-file-input
        label="Clockify Detailed CSV"
        v-model="file"
        accept=".csv"
        prepend-icon="mdi-file-upload"
        :disabled="loading"
        required
        :multiple="false"
      />
      <v-text-field
        v-model.number="bigTaskHours"
        type="number"
        label="Big Task Threshold (hours)"
        :disabled="loading"
        min="0"
        step="0.5"
      />
      <v-btn :loading="loading" type="submit" color="primary" class="mt-2" :disabled="!file">Upload & Analyze</v-btn>
    </v-form>

    <v-divider class="my-4" />

    <div v-if="error" class="text-error mb-4">{{ error }}</div>

    <div v-if="results">
      <v-alert type="success" title="Analysis complete" variant="tonal" class="mb-4" />

      <v-expansion-panels multiple>
        <v-expansion-panel>
          <v-expansion-panel-title>Time Stats</v-expansion-panel-title>
          <v-expansion-panel-text>
            <pre>{{ results.time_stats }}</pre>
          </v-expansion-panel-text>
        </v-expansion-panel>
        <v-expansion-panel>
          <v-expansion-panel-title>Overlap Per User</v-expansion-panel-title>
          <v-expansion-panel-text>
            <pre>{{ results.overlap_per_user }}</pre>
          </v-expansion-panel-text>
        </v-expansion-panel>
        <v-expansion-panel>
          <v-expansion-panel-title>Small Tasks (&lt; 0.01h)</v-expansion-panel-title>
          <v-expansion-panel-text>
            <pre>{{ results.small_tasks_per_user }}</pre>
          </v-expansion-panel-text>
        </v-expansion-panel>
        <v-expansion-panel>
          <v-expansion-panel-title>Big Tasks (&gt; {{ results.big_task_hours }}h)</v-expansion-panel-title>
          <v-expansion-panel-text>
            <pre>{{ results.big_tasks_per_user }}</pre>
          </v-expansion-panel-text>
        </v-expansion-panel>
        <v-expansion-panel>
          <v-expansion-panel-title>Report By User By Date</v-expansion-panel-title>
          <v-expansion-panel-text>
            <pre>{{ results.report_by_user_by_date }}</pre>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>

      <v-divider class="my-4" />
      <h3 class="text-h6 mb-2">Review Entry Reports (this run)</h3>
      <v-btn v-if="entryReportsLink" color="primary" :href="entryReportsLink">
        See Entry Reports
      </v-btn>
    </div>

    <v-divider class="my-4" />

    <h3 class="text-h6 mb-2">Recent Runs</h3>
    <v-alert v-if="runsError" type="error" variant="tonal" class="mb-4" :text="runsError" />
    <v-list v-if="recentRuns.length" lines="two">
      <v-list-item v-for="run in recentRuns" :key="run.run_dir" :title="run.run_dir" :subtitle="`${run.report_files.length} report files`">
        <template #append>
          <v-btn color="primary" variant="text" :href="`/in/reports/${encodeURIComponent(run.run_dir)}/reviews`">Open</v-btn>
        </template>
      </v-list-item>
    </v-list>
    <div v-else class="text-body-2 text-medium-emphasis">No runs available yet.</div>
  </v-card>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import api from '../services/api'

const file = ref(null)
const results = ref(null)
const error = ref('')
const loading = ref(false)
const bigTaskHours = ref(8.0)
const recentRuns = ref([])
const runsError = ref('')

const entryReportsLink = computed(() => {
  const files = results.value?.report_files || []
  if (!files.length) return ''
  const [runDir] = String(files[0].relative_path || '').split('/')
  if (!runDir) return ''
  return `/in/reports/${encodeURIComponent(runDir)}/reviews`
})

const loadRuns = async () => {
  runsError.value = ''
  try {
    const { data } = await api.get('/api/in/runs')
    recentRuns.value = data.items || []
  } catch (requestError) {
    runsError.value = requestError.response?.data?.detail || 'Could not load runs.'
  }
}

const submit = async () => {
  if (!file.value) return
  // Vuetify v-file-input may provide a File or an array of File
  const chosen = Array.isArray(file.value) ? file.value[0] : file.value
  if (!chosen) return
  loading.value = true
  error.value = ''
  results.value = null
  try {
    const formData = new FormData()
    formData.append('file', chosen)
    formData.append('big_task_hours', bigTaskHours.value)
    const { data } = await api.post('/api/in/audit', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    results.value = data
    await loadRuns()
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    loading.value = false
  }
}

onMounted(loadRuns)
</script>
