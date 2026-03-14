import { getStoredSession } from '../../services/api'

export const createReportReviewState = () => ({
  reportPath: '',
  selectedUser: '',
  authSession: getStoredSession(),
  loading: false,
  error: '',
  rows: [],
  reportFiles: [],
  currentRun: null,
  refreshLoading: false,
  viewMode: 'calendar',
  calendarMode: 'month',
  listGroupByDate: false,
  activeLegendUsers: [],
  focusedDateKey: '',
  selectedDayKey: '',
  selectedDayItems: [],
  dayDialogOpen: false,
  currentRunAnalysisDialogOpen: false,
  taskDialogOpen: false,
  selectedTask: null,
})