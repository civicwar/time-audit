<template>
  <div class="d-flex align-center justify-space-between mb-4">
    <h2 class="text-h6">User Report Review</h2>
    <div class="d-flex align-center ga-2">
      <v-btn
        v-if="isAdmin && currentRun && canRefreshCurrentRun"
        color="primary"
        variant="text"
        :loading="refreshLoading"
        @click="$emit('refresh')"
      >
        Refresh
      </v-btn>
      <v-btn color="primary" variant="text" :href="backHref">Back</v-btn>
    </div>
  </div>
</template>

<script setup>
defineProps({
  isAdmin: { type: Boolean, default: false },
  currentRun: { type: Object, default: null },
  canRefreshCurrentRun: { type: Boolean, default: false },
  refreshLoading: { type: Boolean, default: false },
  backHref: { type: String, required: true },
})

defineEmits(['refresh'])
</script>