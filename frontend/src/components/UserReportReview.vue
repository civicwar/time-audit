<template>
  <v-card elevation="2" class="pa-4">
    <div class="d-flex align-center justify-space-between mb-4">
      <h2 class="text-h6">User Report Review</h2>
      <v-btn color="primary" variant="text" :href="backHref">Back</v-btn>
    </div>

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
      <div class="calendar-legend mb-4">
        <div class="d-flex align-center justify-space-between mb-2">
          <div class="text-subtitle-2">Legend</div>
          <div class="d-flex flex-wrap align-center justify-end ga-2">
            <v-btn-toggle
              v-if="viewMode === 'calendar'"
              v-model="calendarMode"
              color="primary"
              density="comfortable"
              mandatory
            >
              <v-btn value="month">Monthly</v-btn>
              <v-btn value="week">Weekly</v-btn>
              <v-btn value="day">Daily</v-btn>
            </v-btn-toggle>
            <v-btn v-if="activeLegendUsers.length" variant="text" size="small" @click="clearCalendarFilters">
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
            :class="{ 'calendar-legend__item--active': isLegendUserActive(user) }"
            @click="toggleLegendUser(user)"
          >
            <span class="calendar-legend__swatch" :style="entryStyle(user)" />
            <span class="text-body-2">{{ user }}</span>
          </button>
        </div>
      </div>
      <div v-if="viewMode === 'calendar'">
        <div v-if="calendarMode !== 'month'" class="d-flex flex-wrap align-center justify-end ga-2 mb-4">
            <v-btn variant="text" @click="shiftCalendarPeriod(-1)">Previous</v-btn>
            <v-btn variant="text" @click="jumpCalendarToToday">Today</v-btn>
            <div class="text-body-2 text-medium-emphasis">{{ calendarPeriodLabel }}</div>
            <v-btn variant="text" @click="shiftCalendarPeriod(1)">Next</v-btn>
        </div>

        <template v-if="calendarMode === 'month'">
          <div
            v-for="month in calendarMonths"
            :key="month.key"
            class="calendar-month mb-6"
          >
            <div class="d-flex align-center justify-space-between mb-3">
              <h3 class="text-subtitle-1">{{ month.label }}</h3>
              <div class="text-body-2 text-medium-emphasis">{{ month.entryCount }} entries</div>
            </div>

            <div class="calendar-grid calendar-grid--header mb-2">
              <div v-for="weekday in weekdayLabels" :key="weekday" class="calendar-weekday text-caption text-medium-emphasis">
                {{ weekday }}
              </div>
            </div>

            <div class="calendar-grid">
              <div
                v-for="day in month.days"
                :key="day.key"
                class="calendar-day"
                :class="{
                  'calendar-day--outside': !day.inCurrentMonth,
                  'calendar-day--empty': !day.items.length,
                  'calendar-day--selected': selectedDayKey === day.key,
                  'calendar-day--clickable': day.items.length,
                }"
                @click="selectCalendarDay(day)"
              >
                <div class="calendar-day__header">
                  <span class="text-caption">{{ day.label }}</span>
                  <span v-if="day.items.length" class="text-caption text-medium-emphasis">{{ day.items.length }}</span>
                </div>

                <div class="calendar-day__entries">
                  <v-tooltip
                    v-for="item in day.items"
                    :key="item.id"
                    location="top"
                    max-width="360"
                  >
                    <template #activator="{ props: tooltipProps }">
                      <button
                        v-bind="tooltipProps"
                        type="button"
                        class="calendar-day__list-item"
                        :style="entryStyle(item.user)"
                        @click.stop="openTaskDialog(item)"
                      >
                        <div class="calendar-day__list-task">{{ truncateDescription(item.description, 40) }}</div>
                        <div class="calendar-day__list-meta">
                          <span>{{ item.user }}</span>
                          <span>{{ item.duration_hm }}</span>
                        </div>
                      </button>
                    </template>
                    <div class="calendar-entry-tooltip">
                      <div class="calendar-entry-tooltip__user">{{ item.user }}</div>
                      <div>{{ item.description }}</div>
                      <div>{{ formatEntryTimeRange(item) }}</div>
                      <div>Total: {{ item.duration_hm }}</div>
                    </div>
                  </v-tooltip>
                </div>
              </div>
            </div>
          </div>
        </template>
        <template v-else-if="calendarMode === 'week'">
          <div v-if="weekCalendarColumns.length" class="time-calendar mb-6">
            <div class="time-calendar__header">
              <div class="time-calendar__time-spacer" />
              <div class="time-calendar__columns" :style="weekCalendarGridStyle">
                <div
                  v-for="column in weekCalendarColumns"
                  :key="column.key"
                  class="time-calendar__column-header"
                >
                  <div class="text-caption text-medium-emphasis">{{ column.weekdayLabel }}</div>
                  <div class="text-subtitle-2">{{ column.label }}</div>
                  <div class="text-caption text-medium-emphasis">{{ column.items.length }} entries</div>
                </div>
              </div>
            </div>
            <div class="time-calendar__body">
              <div class="time-calendar__times">
                <div
                  v-for="slot in weekCalendarSlots"
                  :key="slot.key"
                  class="time-calendar__time-slot"
                  :style="{ height: `${calendarHourHeight}px` }"
                >
                  <span>{{ slot.label }}</span>
                </div>
              </div>
              <div class="time-calendar__columns" :style="weekCalendarGridStyle">
                <div
                  v-for="column in weekCalendarColumns"
                  :key="column.key"
                  class="time-calendar__column"
                  :style="{ height: `${weekCalendarHeight}px` }"
                >
                  <div
                    v-for="line in weekCalendarLines"
                    :key="line.key"
                    class="time-calendar__hour-line"
                    :style="{ top: `${line.offset}px` }"
                  />
                  <button
                    v-for="item in column.layoutItems"
                    :key="item.id"
                    type="button"
                    class="time-calendar__event"
                    :style="calendarEventStyle(item, weekCalendarBounds)"
                    @click="openTaskDialog(item)"
                  >
                    <v-tooltip location="top" max-width="360">
                      <template #activator="{ props: tooltipProps }">
                        <div v-bind="tooltipProps" class="time-calendar__event-card" :style="entryStyle(item.user)">
                          <div class="calendar-entry__user">{{ item.user }}</div>
                        </div>
                      </template>
                      <div class="calendar-entry-tooltip">
                        <div class="calendar-entry-tooltip__user">{{ item.user }}</div>
                        <div>{{ item.description }}</div>
                        <div>{{ formatEntryTimeRange(item) }}</div>
                        <div>Total: {{ item.duration_hm }}</div>
                        <div v-if="item.endDate && item.endDate !== item.date">Ends {{ item.endDate }}</div>
                      </div>
                    </v-tooltip>
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-body-2 text-medium-emphasis">No entries available for this week.</div>
        </template>
        <template v-else>
          <div v-if="dayCalendarColumns.length" class="calendar-day-view">
            <div class="d-flex align-center justify-space-between mb-3">
              <div>
                <div class="text-caption text-medium-emphasis">{{ dayViewWeekdayLabel }}</div>
                <h3 class="text-subtitle-1">{{ calendarPeriodLabel }}</h3>
              </div>
              <div class="text-body-2 text-medium-emphasis">{{ dayEntries.length }} entries</div>
            </div>
            <div class="time-calendar">
              <div class="time-calendar__header">
                <div class="time-calendar__time-spacer" />
                <div class="time-calendar__columns" :style="dayCalendarGridStyle">
                  <div
                    v-for="column in dayCalendarColumns"
                    :key="column.key"
                    class="time-calendar__column-header"
                  >
                    <div class="text-subtitle-2">{{ column.user }}</div>
                    <div class="text-caption text-medium-emphasis">{{ column.items.length }} entries</div>
                  </div>
                </div>
              </div>
              <div class="time-calendar__body">
                <div class="time-calendar__times">
                  <div
                    v-for="slot in dayCalendarSlots"
                    :key="slot.key"
                    class="time-calendar__time-slot"
                    :style="{ height: `${calendarHourHeight}px` }"
                  >
                    <span>{{ slot.label }}</span>
                  </div>
                </div>
                <div class="time-calendar__columns" :style="dayCalendarGridStyle">
                  <div
                    v-for="column in dayCalendarColumns"
                    :key="column.key"
                    class="time-calendar__column"
                    :style="{ height: `${dayCalendarHeight}px` }"
                  >
                    <div
                      v-for="line in dayCalendarLines"
                      :key="line.key"
                      class="time-calendar__hour-line"
                      :style="{ top: `${line.offset}px` }"
                    />
                    <button
                      v-for="item in column.layoutItems"
                      :key="item.id"
                      type="button"
                      class="time-calendar__event"
                      :style="calendarEventStyle(item, dayCalendarBounds)"
                      @click="openTaskDialog(item)"
                    >
                      <v-tooltip location="top" max-width="360">
                        <template #activator="{ props: tooltipProps }">
                          <div v-bind="tooltipProps" class="time-calendar__event-card" :style="entryStyle(item.user)">
                            <div class="calendar-entry__user">{{ item.user }}</div>
                          </div>
                        </template>
                        <div class="calendar-entry-tooltip">
                          <div class="calendar-entry-tooltip__user">{{ item.user }}</div>
                          <div>{{ item.description }}</div>
                          <div>{{ formatEntryTimeRange(item) }}</div>
                          <div>Total: {{ item.duration_hm }}</div>
                          <div v-if="item.endDate && item.endDate !== item.date">Ends {{ item.endDate }}</div>
                        </div>
                      </v-tooltip>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-body-2 text-medium-emphasis">No entries available for this day.</div>
        </template>
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

    <v-dialog v-model="taskDialogOpen" max-width="720">
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
          <v-btn variant="text" @click="closeTaskDialog">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="dayDialogOpen" max-width="960">
      <v-card>
        <v-card-title>{{ dayDialogTitle }}</v-card-title>
        <v-card-text>
          <v-data-table
            :headers="headers"
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
          <v-btn variant="text" @click="closeDayDialog">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import api from '../services/api'

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
const rows = ref([])
const reportFiles = ref([])
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

const runDir = computed(() => {
  const [dir] = (props.reportPath || '').split('/')
  return dir || ''
})

const weekdayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const monthLabelFormatter = new Intl.DateTimeFormat('en', { month: 'long', year: 'numeric' })
const dayLabelFormatter = new Intl.DateTimeFormat('en', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
const dayShortFormatter = new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric' })
const weekdayLongFormatter = new Intl.DateTimeFormat('en', { weekday: 'long' })
const weekdayShortFormatter = new Intl.DateTimeFormat('en', { weekday: 'short' })
const timeLabelFormatter = new Intl.DateTimeFormat('en', { hour: 'numeric' })
const calendarHourHeight = 56
const fullDayCalendarBounds = {
  startHour: 0,
  endHour: 24,
  totalHours: 24,
  totalMinutes: 24 * 60,
}
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

const parseReportDate = (value) => {
  if (!value) return null

  const slashMatch = String(value).match(/^(\d{2})\/(\d{2})\/(\d{4})$/)
  if (slashMatch) {
    const [, day, month, year] = slashMatch
    return new Date(Number(year), Number(month) - 1, Number(day))
  }

  const dashMatch = String(value).match(/^(\d{4})-(\d{2})-(\d{2})$/)
  if (dashMatch) {
    const [, year, month, day] = dashMatch
    return new Date(Number(year), Number(month) - 1, Number(day))
  }

  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

const toCalendarKey = (date) => {
  return [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, '0'),
    String(date.getDate()).padStart(2, '0'),
  ].join('-')
}

const parseReportDateTime = (value) => {
  if (!value) return null

  const dateTimeMatch = String(value).match(
    /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?$/
  )
  if (dateTimeMatch) {
    const [, year, month, day, hour, minute, second = '00'] = dateTimeMatch
    return new Date(
      Number(year),
      Number(month) - 1,
      Number(day),
      Number(hour),
      Number(minute),
      Number(second)
    )
  }

  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

const startOfDay = (date) => new Date(date.getFullYear(), date.getMonth(), date.getDate())

const addDays = (date, days) => {
  const result = new Date(date)
  result.setDate(result.getDate() + days)
  return result
}

const startOfWeek = (date) => {
  const result = startOfDay(date)
  const offset = (result.getDay() + 6) % 7
  result.setDate(result.getDate() - offset)
  return result
}

const clamp = (value, min, max) => Math.min(Math.max(value, min), max)

const toMinutesOfDay = (date) => {
  return (date.getHours() * 60) + date.getMinutes() + (date.getSeconds() / 60)
}

const buildCalendarSlots = (bounds) => {
  return Array.from({ length: bounds.totalHours }, (_, index) => {
    const hour = bounds.startHour + index
    const labelDate = new Date(2026, 0, 1, hour, 0, 0)
    return {
      key: `hour-${hour}`,
      label: timeLabelFormatter.format(labelDate),
      offset: index * calendarHourHeight,
    }
  })
}

const buildCalendarLines = (bounds) => {
  return Array.from({ length: bounds.totalHours + 1 }, (_, index) => ({
    key: `line-${index}`,
    offset: index * calendarHourHeight,
  }))
}

const layoutCalendarItems = (items) => {
  if (!items.length) return []

  const normalized = sortedRowsByTime(items).map((item) => {
    const rawStart = item.startDateTime ? toMinutesOfDay(item.startDateTime) : 0
    const rawEnd = item.endDateTime ? toMinutesOfDay(item.endDateTime) : rawStart + 30
    const startMinutes = clamp(rawStart, 0, 24 * 60)
    const endMinutes = clamp(Math.max(rawEnd, startMinutes + 15), 0, 24 * 60)
    return {
      ...item,
      startMinutes,
      endMinutes,
    }
  })

  const clusters = []
  let currentCluster = []
  let clusterEnd = -1

  normalized.forEach((item) => {
    if (!currentCluster.length || item.startMinutes < clusterEnd) {
      currentCluster.push(item)
      clusterEnd = Math.max(clusterEnd, item.endMinutes)
      return
    }

    clusters.push(currentCluster)
    currentCluster = [item]
    clusterEnd = item.endMinutes
  })

  if (currentCluster.length) {
    clusters.push(currentCluster)
  }

  return clusters.flatMap((cluster) => {
    const laneEnds = []
    const positioned = cluster.map((item) => {
      let laneIndex = laneEnds.findIndex((laneEnd) => laneEnd <= item.startMinutes)
      if (laneIndex === -1) {
        laneIndex = laneEnds.length
        laneEnds.push(item.endMinutes)
      } else {
        laneEnds[laneIndex] = item.endMinutes
      }

      return {
        ...item,
        laneIndex,
      }
    })

    return positioned.map((item) => ({
      ...item,
      laneCount: laneEnds.length,
    }))
  })
}

const userFilteredRows = computed(() => rows.value)

const calendarRows = computed(() => {
  if (!activeLegendUsers.value.length) {
    return userFilteredRows.value
  }
  return userFilteredRows.value.filter((row) => activeLegendUsers.value.includes(row.user))
})

const filteredRows = computed(() => {
  return calendarRows.value
})

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

const entryStyle = (user) => {
  const palette = colorByUser.value[user] || userColorPalette[0]
  return {
    backgroundColor: palette.background,
    borderLeft: `3px solid ${palette.border}`,
    color: palette.text,
  }
}

const isLegendUserActive = (user) => {
  return activeLegendUsers.value.includes(user)
}

const toggleLegendUser = (user) => {
  activeLegendUsers.value = isLegendUserActive(user)
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

const closeTaskDialog = () => {
  taskDialogOpen.value = false
  selectedTask.value = null
}

const closeDayDialog = () => {
  dayDialogOpen.value = false
  selectedDayKey.value = ''
  selectedDayItems.value = []
}

const sortedRowsByTime = (items) => {
  return [...items].sort((left, right) => {
    const leftTime = left.startDateTime?.getTime() ?? parseReportDate(left.date)?.getTime() ?? 0
    const rightTime = right.startDateTime?.getTime() ?? parseReportDate(right.date)?.getTime() ?? 0
    if (leftTime !== rightTime) return leftTime - rightTime
    return left.user.localeCompare(right.user) || left.description.localeCompare(right.description)
  })
}

const syncFocusedDate = () => {
  const available = availableDateKeys.value
  if (!available.length) {
    focusedDateKey.value = ''
    return
  }

  const todayKey = toCalendarKey(new Date())
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

const weekCalendarBounds = computed(() => fullDayCalendarBounds)

const weekCalendarSlots = computed(() => buildCalendarSlots(weekCalendarBounds.value))

const weekCalendarLines = computed(() => buildCalendarLines(weekCalendarBounds.value))

const weekCalendarHeight = computed(() => weekCalendarBounds.value.totalHours * calendarHourHeight)

const weekCalendarColumns = computed(() => {
  return weekDays.value.map((day) => ({
    ...day,
    layoutItems: layoutCalendarItems(day.items),
  }))
})

const weekCalendarGridStyle = computed(() => ({
  gridTemplateColumns: `repeat(${Math.max(weekCalendarColumns.value.length, 1)}, minmax(180px, 1fr))`,
}))

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

const dayEntries = computed(() => {
  if (!focusedDateKey.value) return []
  return sortedRowsByTime(filteredRows.value.filter((row) => row.dayKey === focusedDateKey.value))
})

const dayColumnUsers = computed(() => {
  if (activeLegendUsers.value.length) {
    return [...activeLegendUsers.value].sort((left, right) => left.localeCompare(right))
  }
  return [...legendUsers.value]
})

const dayUserColumns = computed(() => {
  if (!focusedDateKey.value) return []

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
  const todayKey = toCalendarKey(new Date())
  focusedDateKey.value = todayKey
}

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
    if (props.user) {
      activeLegendUsers.value = flatRows.some((row) => row.user === props.user) ? [props.user] : []
    }
    syncFocusedDate()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Could not load run reports.'
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
  } catch (e) {
    error.value = e.response?.data?.detail || 'Could not download selected reports.'
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
  } catch (e) {
    error.value = e.response?.data?.detail || 'Could not download reports zip.'
  }
}

onMounted(loadReport)
watch(() => props.reportPath, loadReport)
watch(filteredRows, syncFocusedDate)
</script>

<style scoped>
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 12px;
}

.calendar-grid--header {
  gap: 8px;
}

.calendar-weekday {
  padding: 0 4px;
}

.calendar-day {
  min-height: 180px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.02);
}

.calendar-day--clickable {
  cursor: pointer;
}

.calendar-day--selected {
  border-color: rgba(31, 111, 235, 0.8);
  box-shadow: inset 0 0 0 1px rgba(31, 111, 235, 0.45);
}

.calendar-day--outside {
  opacity: 0.4;
}

.calendar-day--empty {
  background: rgba(255, 255, 255, 0.01);
}

.calendar-day__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.calendar-day__entries {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.calendar-day__list-item {
  display: block;
  width: 100%;
  padding: 6px 8px;
  border: 0;
  border-radius: 8px;
  color: inherit;
  text-align: left;
  cursor: pointer;
  font-size: 0.8125rem;
  line-height: 1.3;
}

.calendar-day__list-task {
  margin-bottom: 2px;
}

.calendar-day__list-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 0.75rem;
  opacity: 0.9;
}

.calendar-entry {
  border-radius: 10px;
  padding: 8px 10px;
}

.calendar-entry--detailed {
  padding: 12px;
}

.calendar-entry__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 6px;
}

.calendar-entry__user {
  font-size: 0.75rem;
  font-weight: 700;
  margin-bottom: 2px;
}

.calendar-entry__time {
  font-size: 0.75rem;
  opacity: 0.9;
  white-space: nowrap;
}

.calendar-entry__task {
  display: block;
  width: 100%;
  padding: 0;
  border: 0;
  background: transparent;
  text-align: left;
  cursor: pointer;
  font-size: 0.8125rem;
  line-height: 1.25;
  margin-bottom: 4px;
  color: inherit;
}

.calendar-entry__duration {
  font-size: 0.75rem;
  opacity: 0.9;
}

.calendar-entry__compact {
  display: block;
  width: 100%;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.calendar-entry__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 0.75rem;
  opacity: 0.9;
}

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

.task-description-button {
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  text-align: left;
}

.calendar-day-view {
  margin-bottom: 24px;
}

.time-calendar {
  overflow-x: auto;
}

.time-calendar__header,
.time-calendar__body {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr);
  min-width: 960px;
}

.time-calendar__time-spacer {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.time-calendar__columns {
  display: grid;
  gap: 12px;
}

.time-calendar__column-header {
  padding: 0 8px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.time-calendar__times {
  position: relative;
}

.time-calendar__time-slot {
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
  padding-right: 10px;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
}

.time-calendar__column {
  position: relative;
  border-left: 1px solid rgba(255, 255, 255, 0.08);
  border-right: 1px solid rgba(255, 255, 255, 0.04);
  background:
    linear-gradient(to bottom, rgba(255, 255, 255, 0.03), rgba(255, 255, 255, 0.01));
}

.time-calendar__hour-line {
  position: absolute;
  left: 0;
  right: 0;
  height: 1px;
  background: rgba(255, 255, 255, 0.08);
}

.time-calendar__event {
  position: absolute;
  padding: 0;
  border: 0;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.time-calendar__event-card {
  height: 100%;
  border-radius: 10px;
  padding: 8px 10px;
  overflow: hidden;
  display: flex;
  align-items: flex-start;
}

.time-calendar__event-task {
  font-size: 0.8125rem;
  line-height: 1.25;
  margin: 4px 0 6px;
}

.calendar-entry-tooltip {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.calendar-entry-tooltip__user {
  font-weight: 700;
}

@media (max-width: 960px) {
  .calendar-grid {
    grid-template-columns: 1fr;
  }

  .calendar-day {
    min-height: auto;
  }

  .time-calendar__header,
  .time-calendar__body {
    min-width: 720px;
  }
}
</style>
