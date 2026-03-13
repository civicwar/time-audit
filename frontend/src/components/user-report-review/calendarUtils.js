export const weekdayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
export const monthLabelFormatter = new Intl.DateTimeFormat('en', { month: 'long', year: 'numeric' })
export const dayLabelFormatter = new Intl.DateTimeFormat('en', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
export const dayShortFormatter = new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric' })
export const weekdayLongFormatter = new Intl.DateTimeFormat('en', { weekday: 'long' })
export const weekdayShortFormatter = new Intl.DateTimeFormat('en', { weekday: 'short' })
export const timeLabelFormatter = new Intl.DateTimeFormat('en', { hour: 'numeric' })
export const calendarHourHeight = 56
export const fullDayCalendarBounds = {
  startHour: 0,
  endHour: 24,
  totalHours: 24,
  totalMinutes: 24 * 60,
}

export const parseReportDate = (value) => {
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

export const toCalendarKey = (date) => {
  return [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, '0'),
    String(date.getDate()).padStart(2, '0'),
  ].join('-')
}

export const parseReportDateTime = (value) => {
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

export const startOfDay = (date) => new Date(date.getFullYear(), date.getMonth(), date.getDate())

export const addDays = (date, days) => {
  const result = new Date(date)
  result.setDate(result.getDate() + days)
  return result
}

export const startOfWeek = (date) => {
  const result = startOfDay(date)
  const offset = (result.getDay() + 6) % 7
  result.setDate(result.getDate() - offset)
  return result
}

export const clamp = (value, min, max) => Math.min(Math.max(value, min), max)

export const toMinutesOfDay = (date) => {
  return (date.getHours() * 60) + date.getMinutes() + (date.getSeconds() / 60)
}

export const buildCalendarSlots = (bounds) => {
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