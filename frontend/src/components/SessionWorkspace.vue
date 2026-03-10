<template>
  <v-card elevation="2" class="pa-4">
    <div class="d-flex align-center justify-space-between mb-4">
      <div>
        <h2 class="text-h6">Saved Sessions</h2>
        <div class="text-body-2 text-medium-emphasis">Persisted Clockify runs stay private. Only admins can create, rename, or delete them.</div>
      </div>
    </div>

    <v-alert
      v-if="clockifyError"
      type="warning"
      variant="tonal"
      class="mb-4"
      :text="clockifyError"
    />

    <v-card v-if="isAdmin" variant="outlined" class="pa-4 mb-4">
      <div class="text-subtitle-1 mb-3">Create Session From Clockify</div>
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

        <v-text-field
          v-model="sessionName"
          label="Session Name"
          hint="Optional name for this saved session"
          persistent-hint
          :disabled="loading || !clockifyConfigured"
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

    <v-alert
      v-else
      type="info"
      variant="tonal"
      class="mb-4"
      text="Admins can create persisted sessions. You can still review saved sessions below."
    />

    <div v-if="error" class="text-error mb-4">{{ error }}</div>

    <div v-if="results">
      <v-alert type="success" title="Session created" variant="tonal" class="mb-4" />

      <div v-if="results.session" class="text-body-2 text-medium-emphasis mb-4">
        Saved session: {{ results.session.name || results.session.run_dir }}
      </div>

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
      <h3 class="text-h6 mb-2">Review Entry Reports (this session)</h3>
      <v-btn v-if="entryReportsLink" color="primary" :href="entryReportsLink">
        See Entry Reports
      </v-btn>
    </div>

    <v-divider class="my-4" />

    <h3 class="text-h6 mb-2">Persisted Sessions</h3>
    <v-alert v-if="runsError" type="error" variant="tonal" class="mb-4" :text="runsError" />
    <v-alert v-if="renameError" type="error" variant="tonal" class="mb-4" :text="renameError" />
    <v-alert v-if="deleteError" type="error" variant="tonal" class="mb-4" :text="deleteError" />
    <v-list v-if="recentRuns.length" lines="two">
      <v-list-item v-for="run in recentRuns" :key="run.id || run.run_dir">
        <v-list-item-title>{{ run.name || run.run_dir }}</v-list-item-title>
        <v-list-item-subtitle>
          <div>{{ run.run_dir }} • {{ run.report_files.length }} report files</div>
          <div v-if="run.created_by_username || run.created_at || run.clockify_workspace_name">
            <span v-if="run.created_by_username">Created by {{ run.created_by_username }}</span>
            <span v-if="run.created_by_username && run.clockify_workspace_name"> • </span>
            <span v-if="run.clockify_workspace_name">{{ run.clockify_workspace_name }}</span>
            <span v-if="(run.created_by_username || run.clockify_workspace_name) && run.created_at"> • </span>
            <span v-if="run.created_at">{{ formatTimestamp(run.created_at) }}</span>
          </div>
        </v-list-item-subtitle>
        <template #append>
          <div v-if="isAdmin && run.id" class="d-flex align-center ga-2 mr-2">
            <v-text-field
              :model-value="renameDrafts[run.id] ?? run.name ?? ''"
              label="Session Name"
              density="compact"
              variant="outlined"
              hide-details
              style="width: 220px"
              @update:model-value="(value) => updateRenameDraft(run.id, value)"
            />
            <v-btn
              color="secondary"
              variant="text"
              :loading="renameSavingId === run.id"
              @click="saveSessionName(run)"
            >
              Save
            </v-btn>
            <v-btn
              color="error"
              variant="text"
              :loading="deleteSavingId === run.id"
              @click="deleteSession(run)"
            >
              Delete
            </v-btn>
          </div>
          <v-btn color="primary" variant="text" :href="`/in/reports/${encodeURIComponent(run.run_dir)}/reviews`">Open</v-btn>
        </template>
      </v-list-item>
    </v-list>
    <div v-else class="text-body-2 text-medium-emphasis">No persisted sessions available yet.</div>
  </v-card>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import api, { getStoredSession } from '../services/api'

const results = ref(null)
const error = ref('')
const loading = ref(false)
const bigTaskHours = ref(8.0)
const recentRuns = ref([])
const runsError = ref('')
const renameError = ref('')
const renameSavingId = ref(null)
const renameDrafts = ref({})
const deleteError = ref('')
const deleteSavingId = ref(null)
const clockifyError = ref('')
const authSession = ref(getStoredSession())
const clockifyProfile = ref({
  configured: false,
  workspace_name: '',
  user_name: '',
  default_timezone: '',
})
const sessionName = ref('')

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
const isAdmin = computed(() => authSession.value?.user?.role === 'Admin')
const canSubmit = computed(() => {
  return isAdmin.value && clockifyConfigured.value && startDate.value && endDate.value && selectedTimezone.value
})

const formatTimestamp = (value) => {
  if (!value) return ''
  const timestamp = new Date(value)
  if (Number.isNaN(timestamp.getTime())) return value
  return timestamp.toLocaleString()
}

const updateRenameDraft = (sessionId, value) => {
  renameDrafts.value = {
    ...renameDrafts.value,
    [sessionId]: value,
  }
}

const loadClockifyProfile = async () => {
  if (!isAdmin.value) {
    clockifyProfile.value = {
      configured: false,
      workspace_name: '',
      user_name: '',
      default_timezone: '',
    }
    return
  }

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
    renameDrafts.value = Object.fromEntries(
      recentRuns.value
        .filter((item) => item.id)
        .map((item) => [item.id, item.name || ''])
    )
  } catch (requestError) {
    runsError.value = requestError.response?.data?.detail || 'Could not load sessions.'
  }
}

const saveSessionName = async (run) => {
  if (!run.id) return
  renameSavingId.value = run.id
  renameError.value = ''
  try {
    const { data } = await api.patch(`/api/in/sessions/${run.id}`, {
      name: (renameDrafts.value[run.id] || '').trim() || null,
    })
    if (results.value?.session?.id === run.id) {
      results.value.session.name = data.name
    }
    await loadRuns()
  } catch (requestError) {
    renameError.value = requestError.response?.data?.detail || 'Could not update session name.'
  } finally {
    renameSavingId.value = null
  }
}

const deleteSession = async (run) => {
  if (!run.id) return
  deleteSavingId.value = run.id
  deleteError.value = ''
  try {
    await api.delete(`/api/in/sessions/${run.id}`)
    if (results.value?.session?.id === run.id) {
      results.value = null
    }
    await loadRuns()
  } catch (requestError) {
    deleteError.value = requestError.response?.data?.detail || 'Could not delete session.'
  } finally {
    deleteSavingId.value = null
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
      session_name: sessionName.value.trim() || null,
    })
    results.value = data
    if (data.session?.id) {
      updateRenameDraft(data.session.id, data.session.name || '')
    }
    await loadRuns()
  } catch (requestError) {
    error.value = requestError.response?.data?.detail || requestError.message
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadClockifyProfile(), loadRuns()])
})
</script>