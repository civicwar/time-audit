<template>
  <v-card elevation="2" class="pa-4">
    <div class="d-flex align-center justify-space-between mb-4">
      <div>
        <h2 class="text-h6">Upload & Analyze</h2>
        <div class="text-body-2 text-medium-emphasis">Upload a CSV export, run the audit publicly, and review the generated reports for this run.</div>
      </div>
    </div>

    <v-card variant="outlined" class="pa-4 mb-4">
      <div class="text-subtitle-1 mb-3">CSV Audit</div>

      <v-form @submit.prevent="submit">
        <v-row>
          <v-col cols="12" md="8">
            <v-file-input
              v-model="selectedFile"
              accept=".csv,text/csv"
              label="Clockify CSV Export"
              :disabled="loading"
              prepend-icon="mdi-file-delimited"
              required
              show-size
            />
          </v-col>

          <v-col cols="12" md="4">
            <v-text-field
              v-model.number="bigTaskHours"
              type="number"
              label="Big Task Threshold (hours)"
              :disabled="loading"
              min="0"
              step="0.5"
            />
          </v-col>
        </v-row>

        <v-btn
          :loading="loading"
          type="submit"
          color="primary"
          class="mt-2"
          :disabled="!canSubmit"
        >
          Upload & Analyze
        </v-btn>
      </v-form>
    </v-card>

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
  </v-card>
</template>

<script setup>
import { computed, ref } from 'vue'

import api from '../services/api'

const results = ref(null)
const error = ref('')
const loading = ref(false)
const bigTaskHours = ref(8.0)
const selectedFile = ref([])

const entryReportsLink = computed(() => {
  const files = results.value?.report_files || []
  if (!files.length) return ''
  const [runDir] = String(files[0].relative_path || '').split('/')
  if (!runDir) return ''
  return `/reports/${encodeURIComponent(runDir)}/reviews`
})

const selectedCsvFile = computed(() => {
  const value = selectedFile.value
  return Array.isArray(value) ? value[0] || null : value || null
})

const canSubmit = computed(() => Boolean(selectedCsvFile.value))

const submit = async () => {
  if (!canSubmit.value) return
  loading.value = true
  error.value = ''
  results.value = null
  try {
    const payload = new FormData()
    payload.append('file', selectedCsvFile.value)
    payload.append('big_task_hours', String(bigTaskHours.value))
    const { data } = await api.post('/api/audit', payload)
    results.value = data
  } catch (requestError) {
    error.value = requestError.response?.data?.detail || requestError.message
  } finally {
    loading.value = false
  }
}
</script>
