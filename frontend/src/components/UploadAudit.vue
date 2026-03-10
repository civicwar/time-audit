<template>
  <v-card elevation="2" class="pa-4">
    <div class="d-flex align-center justify-space-between mb-4">
      <div>
        <h2 class="text-h6">Audit Workspace</h2>
        <div class="text-body-2 text-medium-emphasis">Fetch Clockify detailed reports directly, choose the date range and timezone, and review past runs.</div>
      </div>
    </div>

    <v-alert
      v-if="clockifyError"
      type="warning"
      variant="tonal"
      class="mb-4"
      :text="clockifyError"
    />

    <v-card variant="outlined" class="pa-4 mb-4">
      <div class="text-subtitle-1 mb-3">Clockify Detailed Report</div>
      <div v-if="clockifyProfile.workspace_name" class="text-body-2 text-medium-emphasis mb-4">
        Connected workspace: {{ clockifyProfile.workspace_name }}
        <span v-if="clockifyProfile.user_name"> as {{ clockifyProfile.user_name }}</span>
      </div>

      <v-form @submit.prevent="submit">
        <v-row>
          <v-col cols="12" md="4">
            <v-text-field
              v-model="startDate"
              type="date"
              label="Start Date"
              :disabled="loading || !clockifyConfigured"
              required
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-text-field
              v-model="endDate"
              type="date"
              label="End Date"
              :disabled="loading || !clockifyConfigured"
              required
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-combobox
              v-model="selectedTimezone"
              :items="timezones"
              label="Timezone"
              :disabled="loading || !clockifyConfigured"
              required
              hide-no-data
            />
          </v-col>
        </v-row>

        <v-text-field
          v-model.number="bigTaskHours"
          type="number"
          label="Big Task Threshold (hours)"
          :disabled="loading || !clockifyConfigured"
          min="0"
          step="0.5"
        />

        <v-btn
          :loading="loading"
          type="submit"
          color="primary"
          class="mt-2"
          :disabled="!canSubmit"
        >
          Fetch & Analyze
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

const results = ref(null)
const error = ref('')
const loading = ref(false)
const bigTaskHours = ref(8.0)
const recentRuns = ref([])
const runsError = ref('')
const clockifyError = ref('')
const clockifyProfile = ref({
  configured: false,
  workspace_name: '',
  user_name: '',
  default_timezone: '',
})

const formatDateInput = (date) => date.toISOString().slice(0, 10)
const today = new Date()
const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1)
const fallbackTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'
const supportedTimezones = typeof Intl.supportedValuesOf === 'function'
  ? Intl.supportedValuesOf('timeZone')
  : ['UTC', 'Europe/Lisbon', 'Europe/London', 'Europe/Berlin', 'America/New_York', 'America/Sao_Paulo']

const startDate = ref(formatDateInput(firstDayOfMonth))
const endDate = ref(formatDateInput(today))
const selectedTimezone = ref(fallbackTimezone)
const timezones = ref(supportedTimezones)

const entryReportsLink = computed(() => {
  const files = results.value?.report_files || []
  if (!files.length) return ''
  const [runDir] = String(files[0].relative_path || '').split('/')
  if (!runDir) return ''
  return `/in/reports/${encodeURIComponent(runDir)}/reviews`
})

const clockifyConfigured = computed(() => clockifyProfile.value.configured)
const canSubmit = computed(() => {
  return clockifyConfigured.value && startDate.value && endDate.value && selectedTimezone.value
})

const loadClockifyProfile = async () => {
  clockifyError.value = ''
  try {
    const { data } = await api.get('/api/in/clockify/profile')
    clockifyProfile.value = data
    if (data.default_timezone) {
      selectedTimezone.value = data.default_timezone
      if (!timezones.value.includes(data.default_timezone)) {
        timezones.value = [data.default_timezone, ...timezones.value]
      }
    }
  } catch (requestError) {
    clockifyProfile.value = {
      configured: false,
      workspace_name: '',
      user_name: '',
      default_timezone: '',
    }
    clockifyError.value = requestError.response?.data?.detail || 'Could not load Clockify configuration.'
  }
}

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
  if (!canSubmit.value) return
  loading.value = true
  error.value = ''
  results.value = null
  try {
    const { data } = await api.post('/api/in/clockify/audit', {
      start_date: startDate.value,
      end_date: endDate.value,
      timezone: selectedTimezone.value,
      big_task_hours: bigTaskHours.value,
    })
    results.value = data
    await loadRuns()
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadClockifyProfile(), loadRuns()])
})
</script>
