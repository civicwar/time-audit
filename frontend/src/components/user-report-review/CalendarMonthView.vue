<template>
  <div
    v-for="month in calendarMonths"
    :key="month.key"
    class="calendar-month mb-6"
  >
    <div class="d-flex align-center justify-space-between mb-3">
      <h3 class="text-subtitle-1">{{ month.label }}</h3>
      <div class="text-body-2 text-medium-emphasis">{{ month.entryCount }} entries</div>
    </div>

    <div class="calendar-grid calendar-grid--header mb-2">
      <div v-for="weekday in weekdayLabels" :key="weekday" class="calendar-weekday text-caption text-medium-emphasis">
        {{ weekday }}
      </div>
    </div>

    <div class="calendar-grid">
      <div
        v-for="day in month.days"
        :key="day.key"
        class="calendar-day"
        :class="{
          'calendar-day--outside': !day.inCurrentMonth,
          'calendar-day--empty': !day.items.length,
          'calendar-day--today': isTodayKey(day.key),
          'calendar-day--selected': selectedDayKey === day.key,
          'calendar-day--clickable': day.items.length,
        }"
        @click="$emit('select-day', day)"
      >
        <div class="calendar-day__header">
          <span class="text-caption">{{ day.label }}</span>
          <span v-if="day.items.length" class="text-caption text-medium-emphasis">{{ day.items.length }}</span>
        </div>

        <div class="calendar-day__entries">
          <v-tooltip
            v-for="item in day.items"
            :key="item.id"
            location="top"
            max-width="360"
          >
            <template #activator="{ props: tooltipProps }">
              <button
                v-bind="tooltipProps"
                type="button"
                class="calendar-day__list-item"
                :style="entryStyle(item.user)"
                @click.stop="$emit('open-task', item)"
              >
                <div class="calendar-day__list-task">{{ truncateDescription(item.description, 40) }}</div>
                <div class="calendar-day__list-meta">
                  <span>{{ item.user }}</span>
                  <span>{{ item.duration_hm }}</span>
                </div>
              </button>
            </template>
            <div class="calendar-entry-tooltip">
              <div class="calendar-entry-tooltip__user">{{ item.user }}</div>
              <div>{{ item.description }}</div>
              <div>{{ formatEntryTimeRange(item) }}</div>
              <div>Total: {{ item.duration_hm }}</div>
            </div>
          </v-tooltip>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  calendarMonths: { type: Array, required: true },
  weekdayLabels: { type: Array, required: true },
  selectedDayKey: { type: String, required: true },
  isTodayKey: { type: Function, required: true },
  entryStyle: { type: Function, required: true },
  truncateDescription: { type: Function, required: true },
  formatEntryTimeRange: { type: Function, required: true },
})

defineEmits(['select-day', 'open-task'])
</script>

<style scoped>
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 12px;
}

.calendar-grid--header {
  gap: 8px;
}

.calendar-weekday {
  padding: 0 4px;
}

.calendar-day {
  min-height: 180px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.02);
}

.calendar-day--clickable {
  cursor: pointer;
}

.calendar-day--selected {
  border-color: rgba(31, 111, 235, 0.8);
  box-shadow: inset 0 0 0 1px rgba(31, 111, 235, 0.45);
}

.calendar-day--today {
  border-color: rgba(210, 153, 34, 0.9);
  box-shadow: inset 0 0 0 1px rgba(210, 153, 34, 0.45);
}

.calendar-day--outside {
  opacity: 0.4;
}

.calendar-day--empty {
  background: rgba(255, 255, 255, 0.01);
}

.calendar-day__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.calendar-day__entries {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.calendar-day__list-item {
  display: block;
  width: 100%;
  padding: 6px 8px;
  border: 0;
  border-radius: 8px;
  color: inherit;
  text-align: left;
  cursor: pointer;
  font-size: 0.8125rem;
  line-height: 1.3;
}

.calendar-day__list-task {
  margin-bottom: 2px;
}

.calendar-day__list-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 0.75rem;
  opacity: 0.9;
}

.calendar-entry-tooltip {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.calendar-entry-tooltip__user {
  font-weight: 700;
}

@media (max-width: 960px) {
  .calendar-grid {
    grid-template-columns: 1fr;
  }

  .calendar-day {
    min-height: auto;
  }
}
</style>