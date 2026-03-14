import api, { getStoredSession } from '../../services/api'
import { addDays, calendarHourHeight, clamp, sortedRowsByTime, startOfDay, toCalendarKey } from '../../utils/calendarUtils'
import { buildFlatRows, downloadBlob, todayKey, userColorPalette } from './helpers'
import { clearSelectionState, resetStoreState } from './mutations'

export const reportReviewActions = {
  clampDateToReportRange(date) {
    if (!date || !this.reportDateBounds) {
      return date
    }

    const normalizedDate = startOfDay(date)
    if (normalizedDate.getTime() < this.reportDateBounds.start.getTime()) {
      return this.reportDateBounds.start
    }
    if (normalizedDate.getTime() > this.reportDateBounds.end.getTime()) {
      return this.reportDateBounds.end
    }
    return normalizedDate
  },

  entryStyle(user) {
    const palette = this.colorByUser[user] || userColorPalette[0]
    return {
      backgroundColor: palette.background,
      borderLeft: `3px solid ${palette.border}`,
      color: palette.text,
    }
  },

  isTodayKey(key) {
    return key === todayKey
  },

  toggleLegendUser(user) {
    if (this.calendarMode === 'week') {
      this.activeLegendUsers = [user]
      return
    }

    this.activeLegendUsers = this.activeLegendUsers.includes(user)
      ? this.activeLegendUsers.filter((item) => item !== user)
      : [...this.activeLegendUsers, user]
  },

  setCalendarMode(mode) {
    this.calendarMode = mode
    if (mode === 'week') {
      this.activeLegendUsers = this.effectiveLegendUsers.length
        ? [this.effectiveLegendUsers[0]]
        : this.legendUsers.length
          ? [this.legendUsers[0]]
          : []
    }
  },

  selectCalendarDay(day) {
    if (!day.items.length) return
    this.focusedDateKey = day.key
    this.selectedDayKey = day.key
    this.selectedDayItems = day.items
    this.dayDialogOpen = true
  },

  clearCalendarFilters() {
    if (this.calendarMode === 'week') {
      this.activeLegendUsers = this.legendUsers.length ? [this.legendUsers[0]] : []
      return
    }

    this.activeLegendUsers = []
  },

  truncateDescription(value, maxLength = 48) {
    if (!value || value.length <= maxLength) return value
    return `${value.slice(0, maxLength - 1)}…`
  },

  openTaskDialog(item) {
    this.selectedTask = item
    this.taskDialogOpen = true
  },

  syncFocusedDate() {
    const available = this.availableDateKeys
    if (!available.length) {
      this.focusedDateKey = ''
      return
    }

    if (this.focusedDateKey && available.includes(this.focusedDateKey)) {
      return
    }

    this.focusedDateKey = available.includes(todayKey) ? todayKey : available[0]
  },

  formatEntryTimeRange(item) {
    const start = item.startTime || 'Unknown'
    const end = item.endTime || 'Unknown'
    return `${start} - ${end}`
  },

  calendarEventStyle(item, bounds) {
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
  },

  shiftCalendarPeriod(direction) {
    if (!this.focusedDate) return
    if (direction < 0 && !this.canShiftCalendarPrevious) return
    if (direction > 0 && !this.canShiftCalendarNext) return
    const offset = this.calendarMode === 'week' ? direction * 7 : direction
    const targetDate = this.clampDateToReportRange(addDays(this.focusedDate, offset))
    this.focusedDateKey = toCalendarKey(targetDate)
  },

  jumpCalendarToToday() {
    const todayDate = this.clampDateToReportRange(new Date())
    if (!todayDate) return
    this.focusedDateKey = toCalendarKey(todayDate)
  },

  setFocusedCalendarDate(value) {
    if (!value) return

    const targetDate = this.clampDateToReportRange(new Date(value))
    if (!targetDate) return
    this.focusedDateKey = toCalendarKey(targetDate)
  },

  openDayView(dayKey) {
    this.setFocusedCalendarDate(dayKey)
    this.calendarMode = 'day'
  },

  async loadReport() {
    if (!this.runDir) {
      this.error = 'Missing run directory.'
      this.rows = []
      return
    }

    this.loading = true
    this.error = ''
    this.rows = []
    this.reportFiles = []
    try {
      const { data: runData } = await api.get(`/api/in/reports/${this.runDir}`)
      const files = runData?.report_files || []
      this.reportFiles = files
      if (!files.length) {
        this.rows = []
        clearSelectionState(this.$state)
        return
      }

      const reportResponses = await Promise.all(
        files.map(async (rf) => {
          const response = await api.get(`/api/in/reports/files/${rf.relative_path}`)
          return { user: rf.user, report: response.data }
        })
      )

      const flatRows = buildFlatRows(reportResponses)

      this.rows = sortedRowsByTime(flatRows)
      clearSelectionState(this.$state)
      if (this.selectedUser) {
        this.activeLegendUsers = flatRows.some((row) => row.user === this.selectedUser) ? [this.selectedUser] : []
      }
      if (this.calendarMode === 'week' && !this.activeLegendUsers.length) {
        this.activeLegendUsers = this.legendUsers.length ? [this.legendUsers[0]] : []
      }
      this.syncFocusedDate()
    } catch (requestError) {
      this.error = requestError.response?.data?.detail || 'Could not load run reports.'
    } finally {
      this.loading = false
    }
  },

  async downloadSelectedReport() {
    if (!this.selectedReportUsers.length) return
    try {
      const response = this.selectedReportUsers.length === 1
        ? await api.get(`/api/in/reports/files/${this.selectedReportFile.relative_path}`, {
            responseType: 'blob',
          })
        : await api.get(`/api/in/reports/${this.runDir}/selected-zip`, {
            params: new URLSearchParams(this.selectedReportUsers.map((user) => ['users', user])),
            responseType: 'blob',
          })

      const fileName = this.selectedReportUsers.length === 1
        ? `${this.selectedReportUsers[0].replace(/\s+/g, '_').toLowerCase()}_report.json`
        : `${this.runDir}_selected_reports.zip`

      downloadBlob(response.data, fileName)
    } catch (requestError) {
      this.error = requestError.response?.data?.detail || 'Could not download selected reports.'
    }
  },

  async downloadAllReportsZip() {
    if (!this.canDownloadAllReportsZip) return
    try {
      const response = await api.get(`/api/in/reports/${this.runDir}/zip`, {
        responseType: 'blob',
      })
      downloadBlob(response.data, `${this.runDir}_reports.zip`)
    } catch (requestError) {
      this.error = requestError.response?.data?.detail || 'Could not download reports zip.'
    }
  },

  async loadCurrentRun() {
    this.currentRun = null
    if (!this.isAdmin || !this.runDir) return

    try {
      const { data } = await api.get('/api/in/runs')
      this.currentRun = (data.items || []).find((item) => item.run_dir === this.runDir) || null
    } catch {
      this.currentRun = null
    }
  },

  async refreshCurrentSession() {
    if (!this.canRefreshCurrentRun) return

    this.refreshLoading = true
    this.error = ''
    try {
      await api.post(`/api/in/sessions/${this.currentRun.id}/refresh`)
      await Promise.all([this.loadCurrentRun(), this.loadReport()])
    } catch (requestError) {
      this.error = requestError.response?.data?.detail || 'Could not refresh session.'
    } finally {
      this.refreshLoading = false
    }
  },

  syncContext(nextReportPath, nextUser = '') {
    this.authSession = getStoredSession()
    const normalizedReportPath = nextReportPath || ''
    const normalizedUser = nextUser || ''
    const contextChanged = this.reportPath !== normalizedReportPath || this.selectedUser !== normalizedUser

    this.reportPath = normalizedReportPath
    this.selectedUser = normalizedUser

    if (!contextChanged) {
      return
    }

    void this.loadCurrentRun()
    void this.loadReport()
  },

  resetStore() {
    resetStoreState(this.$state)
  },
}