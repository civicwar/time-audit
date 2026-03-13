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
        @update:calendar-mode="calendarMode = $event"
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
import { computed, onMounted, ref, watch } from 'vue'

import api, { getStoredSession } from '../services/api'
import CalendarDayView from './user-report-review/CalendarDayView.vue'
import CalendarLegend from './user-report-review/CalendarLegend.vue'
import CalendarMonthView from './user-report-review/CalendarMonthView.vue'
import CalendarWeekView from './user-report-review/CalendarWeekView.vue'
import DayEntriesDialog from './user-report-review/DayEntriesDialog.vue'
import ReportReviewHeader from './user-report-review/ReportReviewHeader.vue'
import TaskDetailsDialog from './user-report-review/TaskDetailsDialog.vue'
import {
  addDays,
  buildCalendarLines,
  buildCalendarSlots,
  buildDailyDaySegments,
  buildWeeklyDaySegments,
  calendarHourHeight,
  clamp,
  dayLabelFormatter,
  dayShortFormatter,
  fullDayCalendarBounds,
  layoutCalendarItems,
  monthLabelFormatter,
  parseReportDate,
  parseReportDateTime,
  sortedRowsByTime,
  startOfDay,
  startOfWeek,
  toCalendarKey,
  weekdayLabels,
  weekdayLongFormatter,
  weekdayShortFormatter,
} from './user-report-review/calendarUtils'

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

const loading = ref(false)
const error = ref('')
const authSession = ref(getStoredSession())
const rows = ref([])
const reportFiles = ref([])
const currentRun = ref(null)
const refreshLoading = ref(false)
const viewMode = ref('calendar')
const calendarMode = ref('month')
const listGroupByDate = ref(false)
const activeLegendUsers = ref([])
const focusedDateKey = ref('')
const selectedDayKey = ref('')
const selectedDayItems = ref([])
const dayDialogOpen = ref(false)
const taskDialogOpen = ref(false)
const selectedTask = ref(null)
const backHref = '/in'

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

const userColorPalette = [
  { background: '#1f6feb22', border: '#1f6feb', text: '#c6dbff' },
  { background: '#23863622', border: '#238636', text: '#b7f0c2' },
  { background: '#d2992222', border: '#d29922', text: '#f7dd9b' },
  { background: '#bf398922', border: '#bf3989', text: '#f3b6dd' },
  { background: '#db6d2822', border: '#db6d28', text: '#ffd1b3' },
  { background: '#8250df22', border: '#8250df', text: '#ddd1ff' },
  { background: '#0969da22', border: '#0969da', text: '#b8d8ff' },
  { background: '#2da44e22', border: '#2da44e', text: '#c0f1cf' },
]

const runDir = computed(() => {
  const [dir] = (props.reportPath || '').split('/')
  return dir || ''
})

const todayKey = toCalendarKey(new Date())
const isAdmin = computed(() => authSession.value?.user?.role === 'Admin')

const canRefreshCurrentRun = computed(() => {
  const run = currentRun.value
  return Boolean(run?.id && run?.start_date && run?.end_date && run?.timezone)
})

const userFilteredRows = computed(() => rows.value)

const calendarRows = computed(() => {
  if (!activeLegendUsers.value.length) {
    return userFilteredRows.value
  }
  return userFilteredRows.value.filter((row) => activeLegendUsers.value.includes(row.user))
})

const filteredRows = computed(() => calendarRows.value)

const selectedReportUsers = computed(() => {
  return activeLegendUsers.value.filter((user) => reportFiles.value.some((rf) => rf.user === user))
})

const selectedReportFile = computed(() => {
  if (selectedReportUsers.value.length !== 1) return null
  return reportFiles.value.find((rf) => rf.user === selectedReportUsers.value[0]) || null
})

const canDownloadSelectedReport = computed(() => selectedReportUsers.value.length > 0)

const allLegendUsersSelected = computed(() => {
  return legendUsers.value.length > 0 && selectedReportUsers.value.length === legendUsers.value.length
})

const showSelectedDownloadButton = computed(() => !allLegendUsersSelected.value)
const canDownloadAllReportsZip = computed(() => Boolean(runDir.value && reportFiles.value.length))

const downloadSelectedButtonText = computed(() => {
  if (!selectedReportUsers.value.length) return 'Select one or more legend users to download reports'
  if (selectedReportUsers.value.length === 1) return `Download ${selectedReportUsers.value[0]} report.json`
  return `Download ${selectedReportUsers.value.length} selected reports.zip`
})

const dateGroups = computed(() => {
  const grouped = calendarRows.value.reduce((acc, row) => {
    if (!acc[row.date]) acc[row.date] = []
    acc[row.date].push(row)
    return acc
  }, {})

  return Object.keys(grouped)
    .sort((left, right) => {
      const leftDate = parseReportDate(left)
      const rightDate = parseReportDate(right)
      if (!leftDate && !rightDate) return String(left).localeCompare(String(right))
      if (!leftDate) return 1
      if (!rightDate) return -1
      return leftDate.getTime() - rightDate.getTime()
    })
    .map((date) => ({
      date,
      parsedDate: parseReportDate(date),
      items: grouped[date],
    }))
})

const listDateGroups = computed(() => {
  const grouped = filteredRows.value.reduce((acc, row) => {
    if (!acc[row.date]) acc[row.date] = []
    acc[row.date].push(row)
    return acc
  }, {})

  return Object.keys(grouped)
    .sort((left, right) => {
      const leftDate = parseReportDate(left)
      const rightDate = parseReportDate(right)
      if (!leftDate && !rightDate) return String(left).localeCompare(String(right))
      if (!leftDate) return 1
      if (!rightDate) return -1
      return leftDate.getTime() - rightDate.getTime()
    })
    .map((date) => ({
      date,
      items: grouped[date],
    }))
})

const legendUsers = computed(() => {
  return Array.from(new Set(userFilteredRows.value.map((row) => row.user))).sort()
})

const showTodayShortcut = computed(() => {
  if (!rows.value.length) return false

  const today = new Date()
  const currentMonth = today.getMonth()
  const currentYear = today.getFullYear()

  const parsedDates = rows.value
    .map((row) => row.startDateTime || parseReportDate(row.date))
    .filter(Boolean)

  if (!parsedDates.length) return false

  return parsedDates.every((date) => date.getFullYear() === currentYear && date.getMonth() === currentMonth)
})

const availableDateKeys = computed(() => {
  return Array.from(
    new Set(
      filteredRows.value
        .map((row) => row.dayKey)
        .filter(Boolean)
    )
  ).sort((left, right) => left.localeCompare(right))
})

const focusedDate = computed(() => {
  const parsed = parseReportDate(focusedDateKey.value)
  return parsed ? startOfDay(parsed) : null
})

const selectedDayLabel = computed(() => {
  if (!selectedDayKey.value) return ''
  const parsed = parseReportDate(selectedDayKey.value)
  if (!parsed) return selectedDayKey.value
  return parsed.toLocaleDateString()
})

const dayDialogTitle = computed(() => {
  return selectedDayLabel.value ? `Entries for ${selectedDayLabel.value}` : 'Entries'
})

const dayViewWeekdayLabel = computed(() => {
  return focusedDate.value ? weekdayLongFormatter.format(focusedDate.value) : ''
})

const colorByUser = computed(() => {
  return Object.fromEntries(
    legendUsers.value.map((user, index) => [user, userColorPalette[index % userColorPalette.length]])
  )
})

const weekDays = computed(() => {
  if (!focusedDate.value) return []

  const weekStart = startOfWeek(focusedDate.value)
  return Array.from({ length: 7 }, (_, index) => {
    const date = addDays(weekStart, index)
    const dayKey = toCalendarKey(date)
    return {
      key: dayKey,
      label: dayShortFormatter.format(date),
      weekdayLabel: weekdayShortFormatter.format(date),
      items: sortedRowsByTime(filteredRows.value.filter((row) => row.dayKey === dayKey)),
    }
  })
})

const weekCalendarBounds = computed(() => fullDayCalendarBounds)
const weekCalendarSlots = computed(() => buildCalendarSlots(weekCalendarBounds.value))
const weekCalendarLines = computed(() => buildCalendarLines(weekCalendarBounds.value))
const weekCalendarHeight = computed(() => weekCalendarBounds.value.totalHours * calendarHourHeight)

const weekCalendarColumns = computed(() => {
  return weekDays.value.map((day) => {
    const dayDate = parseReportDate(day.key)
    const segmentedItems = dayDate ? buildWeeklyDaySegments(filteredRows.value, dayDate) : []
    return {
      ...day,
      layoutItems: layoutCalendarItems(segmentedItems),
    }
  })
})

const weekCalendarGridStyle = computed(() => ({
  gridTemplateColumns: `repeat(${Math.max(weekCalendarColumns.value.length, 1)}, minmax(180px, 1fr))`,
}))

const dayEntries = computed(() => {
  if (!focusedDate.value) return []
  return sortedRowsByTime(buildDailyDaySegments(filteredRows.value, focusedDate.value))
})

const dayColumnUsers = computed(() => {
  if (activeLegendUsers.value.length) {
    return [...activeLegendUsers.value].sort((left, right) => left.localeCompare(right))
  }
  return [...legendUsers.value]
})

const dayUserColumns = computed(() => {
  if (!focusedDate.value) return []

  const itemsByUser = dayEntries.value.reduce((acc, item) => {
    if (!acc[item.user]) acc[item.user] = []
    acc[item.user].push(item)
    return acc
  }, {})

  return dayColumnUsers.value.map((user) => ({
    user,
    items: itemsByUser[user] || [],
  }))
})

const dayCalendarBounds = computed(() => fullDayCalendarBounds)
const dayCalendarSlots = computed(() => buildCalendarSlots(dayCalendarBounds.value))
const dayCalendarLines = computed(() => buildCalendarLines(dayCalendarBounds.value))
const dayCalendarHeight = computed(() => dayCalendarBounds.value.totalHours * calendarHourHeight)

const dayCalendarColumns = computed(() => {
  return dayUserColumns.value.map((column) => ({
    key: column.user,
    user: column.user,
    items: column.items,
    layoutItems: layoutCalendarItems(column.items),
  }))
})

const dayCalendarGridStyle = computed(() => ({
  gridTemplateColumns: `repeat(${Math.max(dayCalendarColumns.value.length, 1)}, minmax(220px, 1fr))`,
}))

const calendarMonths = computed(() => {
  const groups = dateGroups.value
  if (!groups.length) {
    return []
  }

  const itemsByDate = Object.fromEntries(
    groups
      .filter((group) => group.parsedDate)
      .map((group) => [toCalendarKey(group.parsedDate), group.items])
  )
  const monthBuckets = new Map()

  groups.forEach((group) => {
    if (!group.parsedDate) {
      return
    }
    const year = group.parsedDate.getFullYear()
    const month = group.parsedDate.getMonth() + 1
    const key = `${year}-${String(month).padStart(2, '0')}`
    if (!monthBuckets.has(key)) {
      monthBuckets.set(key, { year, month })
    }
  })

  return Array.from(monthBuckets.entries())
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([key, value]) => {
      const monthStart = new Date(value.year, value.month - 1, 1)
      const monthEnd = new Date(value.year, value.month, 0)
      const gridStart = new Date(monthStart)
      const startOffset = (gridStart.getDay() + 6) % 7
      gridStart.setDate(gridStart.getDate() - startOffset)
      const gridEnd = new Date(monthEnd)
      const endOffset = 6 - ((gridEnd.getDay() + 6) % 7)
      gridEnd.setDate(gridEnd.getDate() + endOffset)

      const days = []
      const cursor = new Date(gridStart)
      while (cursor <= gridEnd) {
        const dayKey = toCalendarKey(cursor)
        days.push({
          key: dayKey,
          label: cursor.getDate(),
          inCurrentMonth: cursor.getMonth() === monthStart.getMonth(),
          items: sortedRowsByTime(itemsByDate[dayKey] || []),
        })
        cursor.setDate(cursor.getDate() + 1)
      }

      const entryCount = days.reduce((total, day) => total + day.items.length, 0)
      return {
        key,
        label: monthLabelFormatter.format(monthStart),
        days,
        entryCount,
      }
    })
})

const entryStyle = (user) => {
  const palette = colorByUser.value[user] || userColorPalette[0]
  return {
    backgroundColor: palette.background,
    borderLeft: `3px solid ${palette.border}`,
    color: palette.text,
  }
}

const isTodayKey = (key) => key === todayKey

const toggleLegendUser = (user) => {
  activeLegendUsers.value = activeLegendUsers.value.includes(user)
    ? activeLegendUsers.value.filter((item) => item !== user)
    : [...activeLegendUsers.value, user]
}

const selectCalendarDay = (day) => {
  if (!day.items.length) return
  focusedDateKey.value = day.key
  selectedDayKey.value = day.key
  selectedDayItems.value = day.items
  dayDialogOpen.value = true
}

const clearCalendarFilters = () => {
  activeLegendUsers.value = []
}

const truncateDescription = (value, maxLength = 48) => {
  if (!value || value.length <= maxLength) return value
  return `${value.slice(0, maxLength - 1)}…`
}

const openTaskDialog = (item) => {
  selectedTask.value = item
  taskDialogOpen.value = true
}

const syncFocusedDate = () => {
  const available = availableDateKeys.value
  if (!available.length) {
    focusedDateKey.value = ''
    return
  }

  if (focusedDateKey.value && available.includes(focusedDateKey.value)) {
    return
  }

  focusedDateKey.value = available.includes(todayKey) ? todayKey : available[0]
}

const formatEntryTimeRange = (item) => {
  const start = item.startTime || 'Unknown'
  const end = item.endTime || 'Unknown'
  return `${start} - ${end}`
}

const calendarPeriodLabel = computed(() => {
  if (!focusedDate.value) return 'No entries available'

  if (calendarMode.value === 'day') {
    return dayLabelFormatter.format(focusedDate.value)
  }

  if (calendarMode.value === 'week') {
    const start = startOfWeek(focusedDate.value)
    const end = addDays(start, 6)
    return `${dayShortFormatter.format(start)} - ${dayShortFormatter.format(end)}`
  }

  return 'All months'
})

const calendarEventStyle = (item, bounds) => {
  const boundedStart = clamp(item.startMinutes, bounds.startHour * 60, bounds.endHour * 60)
  const boundedEnd = clamp(item.endMinutes, boundedStart + 15, bounds.endHour * 60)
  const top = ((boundedStart - (bounds.startHour * 60)) / 60) * calendarHourHeight
  const height = Math.max(((boundedEnd - boundedStart) / 60) * calendarHourHeight, 24)
  const widthPercent = 100 / Math.max(item.laneCount || 1, 1)
  const leftPercent = widthPercent * (item.laneIndex || 0)

  return {
    top: `${top}px`,
    height: `${height}px`,
    left: `calc(${leftPercent}% + 4px)`,
    width: `calc(${widthPercent}% - 8px)`,
  }
}

const shiftCalendarPeriod = (direction) => {
  if (!focusedDate.value) return
  const offset = calendarMode.value === 'week' ? direction * 7 : direction
  focusedDateKey.value = toCalendarKey(addDays(focusedDate.value, offset))
}

const jumpCalendarToToday = () => {
  focusedDateKey.value = todayKey
}

const openDayView = (dayKey) => {
  focusedDateKey.value = dayKey
  calendarMode.value = 'day'
}

const loadReport = async () => {
  if (!runDir.value) {
    error.value = 'Missing run directory.'
    rows.value = []
    return
  }

  loading.value = true
  error.value = ''
  rows.value = []
  reportFiles.value = []
  try {
    const { data: runData } = await api.get(`/api/in/reports/${runDir.value}`)
    const files = runData?.report_files || []
    reportFiles.value = files
    if (!files.length) {
      rows.value = []
      return
    }

    const reportResponses = await Promise.all(
      files.map(async (rf) => {
        const response = await api.get(`/api/in/reports/files/${rf.relative_path}`)
        return { user: rf.user, report: response.data }
      })
    )

    const flatRows = []
    reportResponses.forEach(({ user, report }) => {
      Object.entries(report || {}).forEach(([date, tasks]) => {
        ;(tasks || []).forEach((task, index) => {
          const parsedDate = parseReportDate(date)
          const startDateTime = parseReportDateTime(task.start_datetime)
          const endDateTime = parseReportDateTime(task.end_datetime)
          flatRows.push({
            id: `${user}-${date}-${index}-${task.description}`,
            user,
            date,
            description: task.description,
            duration: task.duration,
            duration_hm: task.duration_hm,
            startTime: task.start_time || '',
            endTime: task.end_time || '',
            startDateTime,
            endDateTime,
            endDate: task.end_date || '',
            dayKey: startDateTime ? toCalendarKey(startDateTime) : parsedDate ? toCalendarKey(parsedDate) : '',
          })
        })
      })
    })

    rows.value = sortedRowsByTime(flatRows)
    activeLegendUsers.value = []
    focusedDateKey.value = ''
    selectedDayKey.value = ''
    selectedDayItems.value = []
    if (props.user) {
      activeLegendUsers.value = flatRows.some((row) => row.user === props.user) ? [props.user] : []
    }
    syncFocusedDate()
  } catch (requestError) {
    error.value = requestError.response?.data?.detail || 'Could not load run reports.'
  } finally {
    loading.value = false
  }
}

const downloadSelectedReport = async () => {
  if (!selectedReportUsers.value.length) return
  try {
    const response = selectedReportUsers.value.length === 1
      ? await api.get(`/api/in/reports/files/${selectedReportFile.value.relative_path}`, {
          responseType: 'blob',
        })
      : await api.get(`/api/in/reports/${runDir.value}/selected-zip`, {
          params: new URLSearchParams(selectedReportUsers.value.map((user) => ['users', user])),
          responseType: 'blob',
        })
    const blobUrl = window.URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = selectedReportUsers.value.length === 1
      ? `${selectedReportUsers.value[0].replace(/\s+/g, '_').toLowerCase()}_report.json`
      : `${runDir.value}_selected_reports.zip`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(blobUrl)
  } catch (requestError) {
    error.value = requestError.response?.data?.detail || 'Could not download selected reports.'
  }
}

const downloadAllReportsZip = async () => {
  if (!canDownloadAllReportsZip.value) return
  try {
    const response = await api.get(`/api/in/reports/${runDir.value}/zip`, {
      responseType: 'blob',
    })
    const blobUrl = window.URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = `${runDir.value}_reports.zip`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(blobUrl)
  } catch (requestError) {
    error.value = requestError.response?.data?.detail || 'Could not download reports zip.'
  }
}

const loadCurrentRun = async () => {
  currentRun.value = null
  if (!isAdmin.value || !runDir.value) return

  try {
    const { data } = await api.get('/api/in/runs')
    currentRun.value = (data.items || []).find((item) => item.run_dir === runDir.value) || null
  } catch {
    currentRun.value = null
  }
}

const refreshCurrentSession = async () => {
  if (!canRefreshCurrentRun.value) return

  refreshLoading.value = true
  error.value = ''
  try {
    await api.post(`/api/in/sessions/${currentRun.value.id}/refresh`)
    await Promise.all([loadCurrentRun(), loadReport()])
  } catch (requestError) {
    error.value = requestError.response?.data?.detail || 'Could not refresh session.'
  } finally {
    refreshLoading.value = false
  }
}

onMounted(loadReport)
watch(() => props.reportPath, loadReport)
watch(filteredRows, syncFocusedDate)
watch(runDir, loadCurrentRun, { immediate: true })
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