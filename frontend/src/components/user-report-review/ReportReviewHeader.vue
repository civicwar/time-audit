<template>
  <div class="d-flex align-center justify-space-between mb-4">
    <h2 class="text-h6">User Report Review</h2>
    <div class="d-flex align-center ga-2">
      <v-btn
        v-if="currentRun"
        color="primary"
        variant="text"
        @click="openCurrentRunAnalysisDialog"
      >
        Analysis
      </v-btn>
      <v-btn
        v-if="isAdmin && currentRun && canRefreshCurrentRun"
        color="primary"
        variant="text"
        :loading="refreshLoading"
        @click="refreshCurrentSession"
      >
        Refresh
      </v-btn>
      <v-btn color="primary" variant="text" :href="backHref">Back</v-btn>
    </div>
  </div>
</template>

<script setup>
import { storeToRefs } from 'pinia'

import { useReportReviewStore } from '../../stores/reportReview'

const backHref = '/in'
const store = useReportReviewStore()
const { isAdmin, currentRun, canRefreshCurrentRun, refreshLoading } = storeToRefs(store)
const { openCurrentRunAnalysisDialog, refreshCurrentSession } = store
</script>