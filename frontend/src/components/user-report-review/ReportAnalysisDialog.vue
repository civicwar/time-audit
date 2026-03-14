<template>
  <v-dialog :model-value="dialogOpen" max-width="960" @update:model-value="dialogOpen = $event">
    <v-card>
      <v-card-title>{{ dialogTitle }}</v-card-title>
      <v-card-text>
        <v-expansion-panels v-if="currentRun" multiple>
          <v-expansion-panel>
            <v-expansion-panel-title>Time Stats</v-expansion-panel-title>
            <v-expansion-panel-text>
              <pre>{{ currentRun.time_stats }}</pre>
            </v-expansion-panel-text>
          </v-expansion-panel>
          <v-expansion-panel>
            <v-expansion-panel-title>Overlap Per User</v-expansion-panel-title>
            <v-expansion-panel-text>
              <pre>{{ currentRun.overlap_per_user }}</pre>
            </v-expansion-panel-text>
          </v-expansion-panel>
          <v-expansion-panel>
            <v-expansion-panel-title>Small Tasks (&lt; 0.01h)</v-expansion-panel-title>
            <v-expansion-panel-text>
              <pre>{{ currentRun.small_tasks_per_user }}</pre>
            </v-expansion-panel-text>
          </v-expansion-panel>
          <v-expansion-panel>
            <v-expansion-panel-title>Big Tasks (&gt; {{ currentRun.big_task_hours }}h)</v-expansion-panel-title>
            <v-expansion-panel-text>
              <pre>{{ currentRun.big_tasks_per_user }}</pre>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
        <div v-else class="text-body-2 text-medium-emphasis">No analysis available for this report.</div>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="dialogOpen = false">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { computed } from 'vue'
import { storeToRefs } from 'pinia'

import { useReportReviewStore } from '../../stores/reportReview'

const store = useReportReviewStore()
const { currentRun, currentRunAnalysisDialogOpen } = storeToRefs(store)

const dialogOpen = computed({
  get: () => currentRunAnalysisDialogOpen.value,
  set: (value) => {
    currentRunAnalysisDialogOpen.value = value
  },
})

const dialogTitle = computed(() => {
  if (!currentRun.value) return 'Analysis'
  return `Analysis: ${currentRun.value.name || currentRun.value.run_dir}`
})
</script>