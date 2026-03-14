<template>
  <div v-if="columns.length" class="calendar-day-view">
    <div class="d-flex align-center justify-space-between mb-3">
      <div>
        <div class="text-caption text-medium-emphasis">{{ weekdayLabel }}</div>
        <h3 class="text-subtitle-1">{{ periodLabel }}</h3>
      </div>
      <div class="text-body-2 text-medium-emphasis">{{ entryCount }} entries</div>
    </div>
    <div class="time-calendar">
      <div class="time-calendar__header">
        <div class="time-calendar__time-spacer" />
        <div class="time-calendar__columns" :style="gridStyle">
          <div
            v-for="column in columns"
            :key="column.key"
            class="time-calendar__column-header"
          >
            <div class="text-subtitle-2">{{ column.user }}</div>
            <div class="text-caption text-medium-emphasis">{{ column.items.length }} entries</div>
          </div>
        </div>
      </div>
      <div class="time-calendar__body">
        <div class="time-calendar__times">
          <div
            v-for="slot in slots"
            :key="slot.key"
            class="time-calendar__time-slot"
            :style="{ height: `${calendarHourHeight}px` }"
          >
            <span>{{ slot.label }}</span>
          </div>
        </div>
        <div class="time-calendar__columns" :style="gridStyle">
          <div
            v-for="column in columns"
            :key="column.key"
            class="time-calendar__column"
            :style="{ height: `${height}px` }"
          >
            <div
              v-for="line in lines"
              :key="line.key"
              class="time-calendar__hour-line"
              :style="{ top: `${line.offset}px` }"
            />
            <button
              v-for="item in column.layoutItems"
              :key="item.id"
              type="button"
              class="time-calendar__event"
              :style="calendarEventStyle(item, bounds)"
              @click="openTaskDialog(item)"
            >
              <v-tooltip location="top" max-width="360">
                <template #activator="{ props: tooltipProps }">
                  <div v-bind="tooltipProps" class="time-calendar__event-card time-calendar__event-card--daily" :style="entryStyle(item.user)">
                    <div v-if="item.tags?.length" class="calendar-entry__tags">
                      <span v-for="tag in item.tags" :key="`${item.id}-${tag}`" class="calendar-entry__tag">
                        {{ tag }}
                      </span>
                    </div>
                    <div class="calendar-entry__time">{{ formatEntryTimeRange(item) }}</div>
                    <div class="time-calendar__event-task">{{ truncateDescription(item.description, 72) }}</div>
                  </div>
                </template>
                <div class="calendar-entry-tooltip">
                  <div class="calendar-entry-tooltip__user">{{ item.user }}</div>
                  <div>{{ item.description }}</div>
                  <div v-if="item.tags?.length">Tags: {{ item.tags.join(', ') }}</div>
                  <div>{{ formatEntryTimeRange(item) }}</div>
                  <div>Total: {{ item.duration_hm }}</div>
                  <div v-if="item.endDate && item.endDate !== item.date">Ends {{ item.endDate }}</div>
                </div>
              </v-tooltip>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="text-body-2 text-medium-emphasis">No entries available for this day.</div>
</template>

<script setup>
import { computed } from 'vue'
import { storeToRefs } from 'pinia'

import { useReportReviewStore } from '../../stores/reportReview'
import { calendarHourHeight } from '../../utils/calendarUtils'

const store = useReportReviewStore()
const {
  dayCalendarColumns: columns,
  dayViewWeekdayLabel: weekdayLabel,
  calendarPeriodLabel: periodLabel,
  dayEntries,
  dayCalendarGridStyle: gridStyle,
  dayCalendarSlots: slots,
  dayCalendarLines: lines,
  dayCalendarHeight: height,
  dayCalendarBounds: bounds,
} = storeToRefs(store)
const entryCount = computed(() => dayEntries.value.length)
const { entryStyle, formatEntryTimeRange, truncateDescription, calendarEventStyle, openTaskDialog } = store
</script>

<style scoped>
.calendar-day-view {
  margin-bottom: 24px;
}

.calendar-entry__time {
  font-size: 0.75rem;
  opacity: 0.9;
  white-space: nowrap;
}

.calendar-entry__tags {
  position: absolute;
  top: 8px;
  right: 10px;
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 4px;
  max-width: calc(100% - 20px);
}

.calendar-entry__tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 6px;
  border-radius: 999px;
  background: rgba(128, 128, 128, 0.28);
  border: 1px solid rgba(255, 255, 255, 0.14);
  color: rgba(255, 255, 255, 0.92);
  font-size: 0.6875rem;
  line-height: 1.1;
  white-space: nowrap;
}

.calendar-entry-tooltip {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.calendar-entry-tooltip__user {
  font-weight: 700;
}

.time-calendar {
  overflow-x: auto;
  overflow-y: hidden;
}

.time-calendar__header,
.time-calendar__body {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr);
  min-width: 960px;
}

.time-calendar__time-spacer {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.time-calendar__columns {
  display: grid;
  gap: 12px;
}

.time-calendar__column-header {
  padding: 0 8px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.time-calendar__times {
  position: relative;
}

.time-calendar__time-slot {
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
  padding-right: 10px;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
}

.time-calendar__column {
  position: relative;
  border-left: 1px solid rgba(255, 255, 255, 0.08);
  border-right: 1px solid rgba(255, 255, 255, 0.04);
  background: linear-gradient(to bottom, rgba(255, 255, 255, 0.03), rgba(255, 255, 255, 0.01));
  overflow: hidden;
}

.time-calendar__hour-line {
  position: absolute;
  left: 0;
  right: 0;
  height: 1px;
  background: rgba(255, 255, 255, 0.08);
}

.time-calendar__event {
  position: absolute;
  padding: 0;
  border: 0;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.time-calendar__event-card {
  height: 100%;
  border-radius: 10px;
  padding: 8px 10px;
  overflow: hidden;
  display: flex;
  align-items: flex-start;
}

.time-calendar__event-card--daily {
  position: relative;
  flex-direction: column;
  padding-right: 84px;
}

.time-calendar__event-task {
  font-size: 0.8125rem;
  line-height: 1.25;
  margin: 4px 0 6px;
}

@media (max-width: 960px) {
  .time-calendar__header,
  .time-calendar__body {
    min-width: 720px;
  }
}
</style>