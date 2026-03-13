import {
  addDays,
  buildCalendarLines,
  buildCalendarSlots,
  buildDailyDaySegments,
  buildWeeklyDaySegments,
  calendarHourHeight,
  dayLabelFormatter,
  dayShortFormatter,
  fullDayCalendarBounds,
  layoutCalendarItems,
  monthLabelFormatter,
  parseReportDate,
  sortedRowsByTime,
  startOfDay,
  startOfWeek,
  toCalendarKey,
  weekdayLongFormatter,
  weekdayShortFormatter,
} from '../../utils/calendarUtils'
import { sortDateKeys, todayKey, userColorPalette } from './helpers'

export const reportReviewGetters = {
  runDir: (state) => {
    const [dir] = (state.reportPath || '').split('/')
    return dir || ''
  },

  isAdmin: (state) => state.authSession?.user?.role === 'Admin',

  canRefreshCurrentRun: (state) => {
    const run = state.currentRun
    return Boolean(run?.id && run?.start_date && run?.end_date && run?.timezone)
  },

  userFilteredRows: (state) => state.rows,

  calendarRows() {
    if (!this.activeLegendUsers.length) {
      return this.userFilteredRows
    }
    return this.userFilteredRows.filter((row) => this.activeLegendUsers.includes(row.user))
  },

  filteredRows() {
    return this.calendarRows
  },

  selectedReportUsers(state) {
    return state.activeLegendUsers.filter((user) => state.reportFiles.some((rf) => rf.user === user))
  },

  selectedReportFile() {
    if (this.selectedReportUsers.length !== 1) return null
    return this.reportFiles.find((rf) => rf.user === this.selectedReportUsers[0]) || null
  },

  canDownloadSelectedReport() {
    return this.selectedReportUsers.length > 0
  },

  allLegendUsersSelected() {
    return this.legendUsers.length > 0 && this.selectedReportUsers.length === this.legendUsers.length
  },

  showSelectedDownloadButton() {
    return !this.allLegendUsersSelected
  },

  canDownloadAllReportsZip(state) {
    return Boolean(this.runDir && state.reportFiles.length)
  },

  downloadSelectedButtonText() {
    if (!this.selectedReportUsers.length) return 'Select one or more legend users to download reports'
    if (this.selectedReportUsers.length === 1) return `Download ${this.selectedReportUsers[0]} report.json`
    return `Download ${this.selectedReportUsers.length} selected reports.zip`
  },

  dateGroups() {
    const grouped = this.calendarRows.reduce((acc, row) => {
      if (!acc[row.date]) acc[row.date] = []
      acc[row.date].push(row)
      return acc
    }, {})

    return Object.keys(grouped)
      .sort(sortDateKeys)
      .map((date) => ({
        date,
        parsedDate: parseReportDate(date),
        items: grouped[date],
      }))
  },

  listDateGroups() {
    const grouped = this.filteredRows.reduce((acc, row) => {
      if (!acc[row.date]) acc[row.date] = []
      acc[row.date].push(row)
      return acc
    }, {})

    return Object.keys(grouped)
      .sort(sortDateKeys)
      .map((date) => ({
        date,
        items: grouped[date],
      }))
  },

  legendUsers() {
    return Array.from(new Set(this.userFilteredRows.map((row) => row.user))).sort()
  },

  showTodayShortcut(state) {
    if (!state.rows.length) return false

    const today = new Date()
    const currentMonth = today.getMonth()
    const currentYear = today.getFullYear()

    const parsedDates = state.rows
      .map((row) => row.startDateTime || parseReportDate(row.date))
      .filter(Boolean)

    if (!parsedDates.length) return false

    return parsedDates.every((date) => date.getFullYear() === currentYear && date.getMonth() === currentMonth)
  },

  availableDateKeys() {
    return Array.from(
      new Set(
        this.filteredRows
          .map((row) => row.dayKey)
          .filter(Boolean)
      )
    ).sort((left, right) => left.localeCompare(right))
  },

  focusedDate(state) {
    const parsed = parseReportDate(state.focusedDateKey)
    return parsed ? startOfDay(parsed) : null
  },

  selectedDayLabel(state) {
    if (!state.selectedDayKey) return ''
    const parsed = parseReportDate(state.selectedDayKey)
    if (!parsed) return state.selectedDayKey
    return parsed.toLocaleDateString()
  },

  dayDialogTitle() {
    return this.selectedDayLabel ? `Entries for ${this.selectedDayLabel}` : 'Entries'
  },

  dayViewWeekdayLabel() {
    return this.focusedDate ? weekdayLongFormatter.format(this.focusedDate) : ''
  },

  colorByUser() {
    return Object.fromEntries(
      this.legendUsers.map((user, index) => [user, userColorPalette[index % userColorPalette.length]])
    )
  },

  weekDays() {
    if (!this.focusedDate) return []

    const weekStart = startOfWeek(this.focusedDate)
    return Array.from({ length: 7 }, (_, index) => {
      const date = addDays(weekStart, index)
      const dayKey = toCalendarKey(date)
      return {
        key: dayKey,
        label: dayShortFormatter.format(date),
        weekdayLabel: weekdayShortFormatter.format(date),
        items: sortedRowsByTime(this.filteredRows.filter((row) => row.dayKey === dayKey)),
      }
    })
  },

  weekCalendarBounds: () => fullDayCalendarBounds,

  weekCalendarSlots() {
    return buildCalendarSlots(this.weekCalendarBounds)
  },

  weekCalendarLines() {
    return buildCalendarLines(this.weekCalendarBounds)
  },

  weekCalendarHeight() {
    return this.weekCalendarBounds.totalHours * calendarHourHeight
  },

  weekCalendarColumns() {
    return this.weekDays.map((day) => {
      const dayDate = parseReportDate(day.key)
      const segmentedItems = dayDate ? buildWeeklyDaySegments(this.filteredRows, dayDate) : []
      return {
        ...day,
        layoutItems: layoutCalendarItems(segmentedItems),
      }
    })
  },

  weekCalendarGridStyle() {
    return {
      gridTemplateColumns: `repeat(${Math.max(this.weekCalendarColumns.length, 1)}, minmax(180px, 1fr))`,
    }
  },

  dayEntries() {
    if (!this.focusedDate) return []
    return sortedRowsByTime(buildDailyDaySegments(this.filteredRows, this.focusedDate))
  },

  dayColumnUsers() {
    if (this.activeLegendUsers.length) {
      return [...this.activeLegendUsers].sort((left, right) => left.localeCompare(right))
    }
    return [...this.legendUsers]
  },

  dayUserColumns() {
    if (!this.focusedDate) return []

    const itemsByUser = this.dayEntries.reduce((acc, item) => {
      if (!acc[item.user]) acc[item.user] = []
      acc[item.user].push(item)
      return acc
    }, {})

    return this.dayColumnUsers.map((user) => ({
      user,
      items: itemsByUser[user] || [],
    }))
  },

  dayCalendarBounds: () => fullDayCalendarBounds,

  dayCalendarSlots() {
    return buildCalendarSlots(this.dayCalendarBounds)
  },

  dayCalendarLines() {
    return buildCalendarLines(this.dayCalendarBounds)
  },

  dayCalendarHeight() {
    return this.dayCalendarBounds.totalHours * calendarHourHeight
  },

  dayCalendarColumns() {
    return this.dayUserColumns.map((column) => ({
      key: column.user,
      user: column.user,
      items: column.items,
      layoutItems: layoutCalendarItems(column.items),
    }))
  },

  dayCalendarGridStyle() {
    return {
      gridTemplateColumns: `repeat(${Math.max(this.dayCalendarColumns.length, 1)}, minmax(220px, 1fr))`,
    }
  },

  calendarMonths() {
    const groups = this.dateGroups
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
  },

  calendarPeriodLabel() {
    if (!this.focusedDate) return 'No entries available'

    if (this.calendarMode === 'day') {
      return dayLabelFormatter.format(this.focusedDate)
    }

    if (this.calendarMode === 'week') {
      const start = startOfWeek(this.focusedDate)
      const end = addDays(start, 6)
      return `${dayShortFormatter.format(start)} - ${dayShortFormatter.format(end)}`
    }

    return 'All months'
  },
}

export { calendarHourHeight, todayKey }