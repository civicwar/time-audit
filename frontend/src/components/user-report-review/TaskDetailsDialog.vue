<template>
  <v-dialog :model-value="modelValue" max-width="720" @update:model-value="$emit('update:modelValue', $event)">
    <v-card>
      <v-card-title>Task Details</v-card-title>
      <v-card-text v-if="selectedTask">
        <div class="text-body-2 text-medium-emphasis mb-3">
          {{ selectedTask.user }} • {{ selectedTask.date }} • {{ selectedTask.duration_hm }}
        </div>
        <div class="text-body-1">{{ selectedTask.description }}</div>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="$emit('update:modelValue', false)">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
defineProps({
  modelValue: { type: Boolean, required: true },
  selectedTask: { type: Object, default: null },
})

defineEmits(['update:modelValue'])
</script>