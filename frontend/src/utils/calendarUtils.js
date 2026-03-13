import dayjs from 'dayjs'
import customParseFormat from 'dayjs/plugin/customParseFormat'
import isoWeek from 'dayjs/plugin/isoWeek'

dayjs.extend(customParseFormat)
dayjs.extend(isoWeek)

export const weekdayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
export const monthLabelFormatter = {
  format: (value) => dayjs(value).format('MMMM YYYY'),
}
export const dayLabelFormatter = {
  format: (value) => dayjs(value).format('dddd, MMMM D, YYYY'),
}
export const dayShortFormatter = {
  format: (value) => dayjs(value).format('MMM D'),
}
export const weekdayLongFormatter = {
  format: (value) => dayjs(value).format('dddd'),
}
export const weekdayShortFormatter = {
  format: (value) => dayjs(value).format('ddd'),
}
export const timeLabelFormatter = {
  format: (value) => dayjs(value).format('h A'),
}
export const calendarHourHeight = 56
export const fullDayCalendarBounds = {
  startHour: 0,
  endHour: 24,
  totalHours: 24,
  totalMinutes: 24 * 60,
}

const parseWithFormats = (value, formats) => {
  for (const format of formats) {
    const parsed = dayjs(value, format, true)
    if (parsed.isValid()) {
      return parsed
    }
  }

  const fallback = dayjs(value)
  return fallback.isValid() ? fallback : null
}

export const parseReportDate = (value) => {
  if (!value) return null

  const parsed = parseWithFormats(String(value), ['DD/MM/YYYY', 'YYYY-MM-DD'])
  return parsed ? parsed.toDate() : null
}

export const toCalendarKey = (date) => {
  return dayjs(date).format('YYYY-MM-DD')
}

export const parseReportDateTime = (value) => {
  if (!value) return null

  const parsed = parseWithFormats(String(value), ['YYYY-MM-DD HH:mm:ss', 'YYYY-MM-DDTHH:mm:ss'])
  return parsed ? parsed.toDate() : null
}

export const startOfDay = (date) => dayjs(date).startOf('day').toDate()

export const addDays = (date, days) => dayjs(date).add(days, 'day').toDate()

export const startOfWeek = (date) => dayjs(date).startOf('isoWeek').toDate()

export const clamp = (value, min, max) => Math.min(Math.max(value, min), max)

export const toMinutesOfDay = (date) => {
  const value = dayjs(date)
  return (value.hour() * 60) + value.minute() + (value.second() / 60)
}

export const buildCalendarSlots = (bounds) => {
  return Array.from({ length: bounds.totalHours }, (_, index) => {
    const hour = bounds.startHour + index
    const labelDate = dayjs().year(2026).month(0).date(1).hour(hour).minute(0).second(0)
    return {
      key: `hour-${hour}`,
      label: timeLabelFormatter.format(labelDate.toDate()),
      offset: index * calendarHourHeight,
    }
  })
}

export const buildCalendarLines = (bounds) => {
  return Array.from({ length: bounds.totalHours + 1 }, (_, index) => ({
    key: `line-${index}`,
    offset: index * calendarHourHeight,
  }))
}

export const sortedRowsByTime = (items) => {
  return [...items].sort((left, right) => {
    const leftTime = left.startDateTime?.getTime() ?? parseReportDate(left.date)?.getTime() ?? 0
    const rightTime = right.startDateTime?.getTime() ?? parseReportDate(right.date)?.getTime() ?? 0
    if (leftTime !== rightTime) return leftTime - rightTime
    return left.user.localeCompare(right.user) || left.description.localeCompare(right.description)
  })
}

export const layoutCalendarItems = (items) => {
  if (!items.length) return []

  const normalized = sortedRowsByTime(items).map((item) => {
    const rawStart = Number.isFinite(item.startMinutes)
      ? item.startMinutes
      : item.startDateTime
        ? toMinutesOfDay(item.startDateTime)
        : 0
    const rawEnd = Number.isFinite(item.endMinutes)
      ? item.endMinutes
      : item.endDateTime
        ? toMinutesOfDay(item.endDateTime)
        : rawStart + 30
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

export const buildWeeklyDaySegments = (items, dayDate) => {
  const dayStart = startOfDay(dayDate)
  const nextDayStart = addDays(dayStart, 1)

  return items.flatMap((item) => {
    if (!item.startDateTime || !item.endDateTime) {
      return []
    }

    if (item.endDateTime <= dayStart || item.startDateTime >= nextDayStart) {
      return []
    }

    const segmentStart = item.startDateTime > dayStart ? item.startDateTime : dayStart
    const segmentEnd = item.endDateTime < nextDayStart ? item.endDateTime : nextDayStart
    const startMinutes = toMinutesOfDay(segmentStart)
    const endMinutes = segmentEnd.getTime() === nextDayStart.getTime() ? 24 * 60 : toMinutesOfDay(segmentEnd)

    return [
      {
        ...item,
        id: `${item.id}-${toCalendarKey(dayDate)}`,
        segmentDateKey: toCalendarKey(dayDate),
        startDateTime: segmentStart,
        endDateTime: segmentEnd,
        startMinutes,
        endMinutes: Math.max(endMinutes, startMinutes + 15),
      },
    ]
  })
}

export const buildDailyDaySegments = (items, dayDate) => {
  return buildWeeklyDaySegments(items, dayDate)
}