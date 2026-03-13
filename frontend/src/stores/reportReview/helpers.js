import { parseReportDate, parseReportDateTime, toCalendarKey } from '../../utils/calendarUtils'

export const userColorPalette = [
  { background: '#1f6feb22', border: '#1f6feb', text: '#c6dbff' },
  { background: '#23863622', border: '#238636', text: '#b7f0c2' },
  { background: '#d2992222', border: '#d29922', text: '#f7dd9b' },
  { background: '#bf398922', border: '#bf3989', text: '#f3b6dd' },
  { background: '#db6d2822', border: '#db6d28', text: '#ffd1b3' },
  { background: '#8250df22', border: '#8250df', text: '#ddd1ff' },
  { background: '#0969da22', border: '#0969da', text: '#b8d8ff' },
  { background: '#2da44e22', border: '#2da44e', text: '#c0f1cf' },
]

export const todayKey = toCalendarKey(new Date())

export const sortDateKeys = (left, right) => {
  const leftDate = parseReportDate(left)
  const rightDate = parseReportDate(right)
  if (!leftDate && !rightDate) return String(left).localeCompare(String(right))
  if (!leftDate) return 1
  if (!rightDate) return -1
  return leftDate.getTime() - rightDate.getTime()
}

export const buildFlatRows = (reportResponses) => {
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

  return flatRows
}

export const downloadBlob = (blob, fileName) => {
  const blobUrl = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = blobUrl
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(blobUrl)
}