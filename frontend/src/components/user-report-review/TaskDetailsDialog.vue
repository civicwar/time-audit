<template>
  <v-dialog :model-value="dialogOpen" max-width="720" @update:model-value="dialogOpen = $event">
    <v-card>
      <v-card-title>Task Details</v-card-title>
      <v-card-text v-if="selectedTask">
        <div class="text-body-2 text-medium-emphasis mb-3">
          {{ selectedTask.user }} • {{ selectedTask.date }} • {{ selectedTask.duration_hm }}
        </div>
        <div class="text-body-1">{{ selectedTask.description }}</div>
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
const { taskDialogOpen, selectedTask } = storeToRefs(store)
const dialogOpen = computed({
  get: () => taskDialogOpen.value,
  set: (value) => {
    taskDialogOpen.value = value
  },
})
</script>