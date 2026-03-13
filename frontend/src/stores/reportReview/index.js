import { defineStore } from 'pinia'

import { reportReviewActions } from './actions'
import { reportReviewGetters } from './getters'
import { createReportReviewState } from './state'

export const useReportReviewStore = defineStore('reportReview', {
  state: createReportReviewState,
  getters: reportReviewGetters,
  actions: reportReviewActions,
})