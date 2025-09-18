<template>
  <v-card elevation="2" class="pa-4">
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
      <h3 class="text-h6 mb-2">Download Per-User JSON Reports (this run)</h3>
      <v-chip-group column v-if="results.report_files && results.report_files.length">
        <v-chip
          v-for="rf in results.report_files"
          :key="rf.relative_path"
          :href="`/reports/${rf.relative_path}`"
          target="_blank"
          label
          variant="outlined"
          color="primary"
        >{{ rf.user }}</v-chip>
      </v-chip-group>
    </div>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const file = ref(null)
const results = ref(null)
const error = ref('')
const loading = ref(false)
const bigTaskHours = ref(8.0)

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
    const { data } = await axios.post('/api/audit', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    results.value = data
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    loading.value = false
  }
}

// Deprecated: dynamic reportLink replaced by server-provided filenames with timestamps
</script>
