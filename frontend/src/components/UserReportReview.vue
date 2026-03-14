<template>
  <v-card elevation="2" class="pa-4">
    <report-review-header
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
        />

        <calendar-week-view
          v-else-if="calendarMode === 'week'"
        />

        <calendar-day-view v-else />

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
    />

    <day-entries-dialog
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
import { groupedReportReviewHeaders, reportReviewHeaders } from './user-report-review/tableHeaders'
import { useReportReviewStore } from '../stores/reportReview'

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

const store = useReportReviewStore()

const {
  loading,
  error,
  viewMode,
  calendarMode,
  listGroupByDate,
  filteredRows,
  showSelectedDownloadButton,
  canDownloadSelectedReport,
  downloadSelectedButtonText,
  canDownloadAllReportsZip,
  listDateGroups,
  showTodayShortcut,
  calendarPeriodLabel,
} = storeToRefs(store)

const {
  truncateDescription,
  openTaskDialog,
  shiftCalendarPeriod,
  jumpCalendarToToday,
  downloadSelectedReport,
  downloadAllReportsZip,
  syncContext,
  resetStore,
} = store

const headers = reportReviewHeaders
const groupedHeaders = groupedReportReviewHeaders

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