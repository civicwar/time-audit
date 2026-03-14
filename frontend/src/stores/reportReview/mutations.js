import { createReportReviewState } from './state'

export const clearSelectionState = (state) => {
  state.activeLegendUsers = []
  state.focusedDateKey = ''
  state.selectedDayKey = ''
  state.selectedDayItems = []
  state.dayDialogOpen = false
  state.taskDialogOpen = false
  state.selectedTask = null
}

export const resetStoreState = (state) => {
  Object.assign(state, createReportReviewState())
}