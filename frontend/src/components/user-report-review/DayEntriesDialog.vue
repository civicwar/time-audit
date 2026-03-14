<template>
  <v-dialog :model-value="dialogOpen" max-width="960" @update:model-value="dialogOpen = $event">
    <v-card>
      <v-card-title>{{ dayDialogTitle }}</v-card-title>
      <v-card-text>
        <v-data-table
          :headers="reportReviewHeaders"
          :items="selectedDayItems"
          density="comfortable"
          item-value="id"
          :sort-by="[{ key: 'user', order: 'asc' }, { key: 'duration', order: 'desc' }]"
        >
          <template #item.description="{ item }">
            <button
              type="button"
              class="task-description-button"
              :title="item.description"
              @click="openTaskDialog(item)"
            >
              {{ truncateDescription(item.description) }}
            </button>
          </template>
        </v-data-table>
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
import { reportReviewHeaders } from '../../data/reportReviewTableHeaders'

const store = useReportReviewStore()
const { dayDialogOpen, dayDialogTitle, selectedDayItems } = storeToRefs(store)
const { truncateDescription, openTaskDialog } = store
const dialogOpen = computed({
  get: () => dayDialogOpen.value,
  set: (value) => {
    dayDialogOpen.value = value
  },
})
</script>

<style scoped>
.task-description-button {
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  text-align: left;
}
</style>