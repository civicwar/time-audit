<template>
  <div class="calendar-legend mb-4">
    <div class="d-flex align-center justify-space-between mb-2">
      <div class="text-subtitle-2">Legend</div>
      <div class="d-flex flex-wrap align-center justify-end ga-2">
        <v-btn-toggle
          v-if="viewMode === 'calendar'"
          :model-value="calendarMode"
          color="primary"
          density="comfortable"
          mandatory
          @update:model-value="setCalendarMode"
        >
          <v-btn value="month">Monthly</v-btn>
          <v-btn value="week">Weekly</v-btn>
          <v-btn value="day">Daily</v-btn>
        </v-btn-toggle>
        <v-btn v-if="showClearFilters" variant="text" size="small" @click="clearCalendarFilters">
          Clear filters
        </v-btn>
      </div>
    </div>
    <div class="d-flex flex-wrap ga-2">
      <button
        v-for="user in legendUsers"
        :key="user"
        type="button"
        class="calendar-legend__item"
        :class="{ 'calendar-legend__item--active': effectiveLegendUsers.includes(user) }"
        @click="toggleLegendUser(user)"
      >
        <span class="calendar-legend__swatch" :style="entryStyle(user)" />
        <span class="text-body-2">{{ user }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { storeToRefs } from 'pinia'

import { useReportReviewStore } from '../../stores/reportReview'

const store = useReportReviewStore()
const { legendUsers, activeLegendUsers, effectiveLegendUsers, viewMode, calendarMode } = storeToRefs(store)
const { entryStyle, toggleLegendUser, setCalendarMode, clearCalendarFilters } = store
const showClearFilters = computed(() => {
  if (calendarMode.value === 'week') {
    return false
  }
  return activeLegendUsers.value.length > 0
})
</script>

<style scoped>
.calendar-legend__item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid transparent;
  color: inherit;
  cursor: pointer;
}

.calendar-legend__item--active {
  border-color: rgba(255, 255, 255, 0.18);
  background: rgba(255, 255, 255, 0.08);
}

.calendar-legend__swatch {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  display: inline-block;
}
</style>