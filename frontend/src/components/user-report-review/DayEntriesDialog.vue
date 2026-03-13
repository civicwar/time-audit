<template>
  <v-dialog :model-value="modelValue" max-width="960" @update:model-value="$emit('update:modelValue', $event)">
    <v-card>
      <v-card-title>{{ title }}</v-card-title>
      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="items"
          density="comfortable"
          item-value="id"
          :sort-by="[{ key: 'user', order: 'asc' }, { key: 'duration', order: 'desc' }]"
        >
          <template #item.description="{ item }">
            <button
              type="button"
              class="task-description-button"
              :title="item.description"
              @click="$emit('open-task', item)"
            >
              {{ truncateDescription(item.description) }}
            </button>
          </template>
        </v-data-table>
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
  title: { type: String, required: true },
  headers: { type: Array, required: true },
  items: { type: Array, required: true },
  truncateDescription: { type: Function, required: true },
})

defineEmits(['update:modelValue', 'open-task'])
</script>

<style scoped>
.task-description-button {
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  text-align: left;
}
</style>