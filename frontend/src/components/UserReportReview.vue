<template>
  <v-card elevation="2" class="pa-4">
    <report-review-header
      :is-admin="isAdmin"
      :current-run="currentRun"
      :can-refresh-current-run="canRefreshCurrentRun"
      :refresh-loading="refreshLoading"
      :back-href="backHref"
      @refresh="refreshCurrentSession"
    />

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
        <v-btn-toggle
          v-model="viewMode"
          color="primary"
          density="comfortable"
          mandatory
        >
          <v-btn value="calendar">Calendar</v-btn>
          <v-btn value="list">List</v-btn>
        </v-btn-toggle>
        <v-switch
          v-if="viewMode === 'list'"
          v-model="listGroupByDate"
          color="primary"
          hide-details
          label="Group by date"
        />
        <v-btn
          v-if="showSelectedDownloadButton"
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

      <calendar-legend
        :legend-users="legendUsers"
        :active-legend-users="activeLegendUsers"
        :view-mode="viewMode"
        :calendar-mode="calendarMode"
        :entry-style="entryStyle"
        @update:calendar-mode="setCalendarMode"
        @toggle-user="toggleLegendUser"
        @clear-filters="clearCalendarFilters"
      />

      <div v-if="viewMode === 'calendar'">
        <div v-if="calendarMode !== 'month'" class="d-flex flex-wrap align-center justify-end ga-2 mb-4">
          <div class="text-body-2 text-medium-emphasis me-auto">{{ calendarPeriodLabel }}</div>
          <v-btn icon="mdi-chevron-left" variant="text" @click="shiftCalendarPeriod(-1)" />
          <v-tooltip v-if="showTodayShortcut" text="Today" location="top">
            <template #activator="{ props: tooltipProps }">
              <v-btn v-bind="tooltipProps" icon="mdi-calendar-today" variant="text" @click="jumpCalendarToToday" />
            </template>
          </v-tooltip>
          <v-btn icon="mdi-chevron-right" variant="text" @click="shiftCalendarPeriod(1)" />
        </div>

        <calendar-month-view
          v-if="calendarMode === 'month'"
          :calendar-months="calendarMonths"
          :weekday-labels="weekdayLabels"
          :selected-day-key="selectedDayKey"
          :is-today-key="isTodayKey"
          :entry-style="entryStyle"
          :truncate-description="truncateDescription"
          :format-entry-time-range="formatEntryTimeRange"
          @select-day="selectCalendarDay"
          @open-task="openTaskDialog"
        />

        <calendar-week-view
          v-else-if="calendarMode === 'week'"
          :columns="weekCalendarColumns"
          :grid-style="weekCalendarGridStyle"
          :slots="weekCalendarSlots"
          :lines="weekCalendarLines"
          :height="weekCalendarHeight"
          :bounds="weekCalendarBounds"
          :calendar-hour-height="calendarHourHeight"
          :is-today-key="isTodayKey"
          :entry-style="entryStyle"
          :format-entry-time-range="formatEntryTimeRange"
          :calendar-event-style="calendarEventStyle"
          @open-task="openTaskDialog"
          @select-day="openDayView"
        />

        <calendar-day-view
          v-else
          :columns="dayCalendarColumns"
          :weekday-label="dayViewWeekdayLabel"
          :period-label="calendarPeriodLabel"
          :entry-count="dayEntries.length"
          :grid-style="dayCalendarGridStyle"
          :slots="dayCalendarSlots"
          :lines="dayCalendarLines"
          :height="dayCalendarHeight"
          :bounds="dayCalendarBounds"
          :calendar-hour-height="calendarHourHeight"
          :entry-style="entryStyle"
          :format-entry-time-range="formatEntryTimeRange"
          :truncate-description="truncateDescription"
          :calendar-event-style="calendarEventStyle"
          @open-task="openTaskDialog"
        />

        <div class="d-flex align-center justify-space-between mb-2">
          <div class="text-body-2 text-medium-emphasis">
            <template v-if="calendarMode === 'month'">Click a day to open its entries.</template>
            <template v-else>Entries show their start and end times for the selected period.</template>
          </div>
          <div class="text-body-2 text-medium-emphasis">{{ filteredRows.length }} matching entries</div>
        </div>
      </div>

      <v-data-table
        v-else-if="!listGroupByDate"
        :headers="headers"
        :items="filteredRows"
        density="comfortable"
        item-value="id"
        :sort-by="[{ key: 'date', order: 'asc' }, { key: 'user', order: 'asc' }]"
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

      <v-expansion-panels v-else multiple>
        <v-expansion-panel
          v-for="group in listDateGroups"
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
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </div>

    <task-details-dialog
      v-model="taskDialogOpen"
      :selected-task="selectedTask"
    />

    <day-entries-dialog
      v-model="dayDialogOpen"
      :title="dayDialogTitle"
      :headers="headers"
      :items="selectedDayItems"
      :truncate-description="truncateDescription"
      @open-task="openTaskDialog"
    />
  </v-card>
</template>

<script setup>
import { onUnmounted, watch } from 'vue'
import { storeToRefs } from 'pinia'

import CalendarDayView from './user-report-review/CalendarDayView.vue'
import CalendarLegend from './user-report-review/CalendarLegend.vue'
import CalendarMonthView from './user-report-review/CalendarMonthView.vue'
import CalendarWeekView from './user-report-review/CalendarWeekView.vue'
import DayEntriesDialog from './user-report-review/DayEntriesDialog.vue'
import ReportReviewHeader from './user-report-review/ReportReviewHeader.vue'
import TaskDetailsDialog from './user-report-review/TaskDetailsDialog.vue'
import { useReportReviewStore } from '../stores/reportReview'
import { calendarHourHeight, weekdayLabels } from '../utils/calendarUtils'

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

const backHref = '/in'
const store = useReportReviewStore()

const {
  loading,
  error,
  currentRun,
  refreshLoading,
  viewMode,
  calendarMode,
  listGroupByDate,
  activeLegendUsers,
  selectedDayKey,
  selectedDayItems,
  dayDialogOpen,
  taskDialogOpen,
  selectedTask,
  isAdmin,
  canRefreshCurrentRun,
  filteredRows,
  showSelectedDownloadButton,
  canDownloadSelectedReport,
  downloadSelectedButtonText,
  canDownloadAllReportsZip,
  listDateGroups,
  legendUsers,
  showTodayShortcut,
  dayDialogTitle,
  dayViewWeekdayLabel,
  weekCalendarColumns,
  weekCalendarGridStyle,
  weekCalendarSlots,
  weekCalendarLines,
  weekCalendarHeight,
  weekCalendarBounds,
  dayEntries,
  dayCalendarColumns,
  dayCalendarGridStyle,
  dayCalendarSlots,
  dayCalendarLines,
  dayCalendarHeight,
  dayCalendarBounds,
  calendarMonths,
  calendarPeriodLabel,
} = storeToRefs(store)

const {
  toggleLegendUser,
  setCalendarMode,
  selectCalendarDay,
  clearCalendarFilters,
  truncateDescription,
  openTaskDialog,
  formatEntryTimeRange,
  calendarEventStyle,
  shiftCalendarPeriod,
  jumpCalendarToToday,
  openDayView,
  entryStyle,
  isTodayKey,
  downloadSelectedReport,
  downloadAllReportsZip,
  refreshCurrentSession,
  syncContext,
  resetStore,
} = store

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

watch(
  () => [props.reportPath, props.user],
  ([reportPath, user]) => {
    syncContext(reportPath, user)
  },
  { immediate: true }
)

watch(filteredRows, () => {
  store.syncFocusedDate()
})

onUnmounted(() => {
  resetStore()
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