<template>
  <div v-if="columns.length" class="time-calendar mb-6">
    <div class="time-calendar__header">
      <div class="time-calendar__time-spacer" />
      <div class="time-calendar__columns" :style="gridStyle">
        <v-tooltip
          v-for="column in columns"
          :key="column.key"
          text="Open daily view"
          location="top"
        >
          <template #activator="{ props: tooltipProps }">
            <div
              v-bind="tooltipProps"
              class="time-calendar__column-header"
              :class="{ 'time-calendar__column-header--today': isTodayKey(column.key) }"
              role="button"
              tabindex="0"
              @click="openDayView(column.key)"
              @keydown.enter.prevent="openDayView(column.key)"
              @keydown.space.prevent="openDayView(column.key)"
            >
              <div class="text-caption text-medium-emphasis">{{ column.weekdayLabel }}</div>
              <div class="text-subtitle-2">{{ column.label }}</div>
              <div class="text-caption text-medium-emphasis">{{ column.items.length }} entries</div>
            </div>
          </template>
        </v-tooltip>
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
          :class="{ 'time-calendar__column--today': isTodayKey(column.key) }"
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
                <div v-bind="tooltipProps" class="time-calendar__event-card" :style="entryStyle(item.user)">
                  <div class="calendar-entry__user">{{ item.user }}</div>
                </div>
              </template>
              <div class="calendar-entry-tooltip">
                <div class="calendar-entry-tooltip__user">{{ item.user }}</div>
                <div>{{ item.description }}</div>
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
  <div v-else class="text-body-2 text-medium-emphasis">No entries available for this week.</div>
</template>

<script setup>
import { storeToRefs } from 'pinia'

import { useReportReviewStore } from '../../stores/reportReview'
import { calendarHourHeight } from '../../utils/calendarUtils'

const store = useReportReviewStore()
const {
  weekCalendarColumns: columns,
  weekCalendarGridStyle: gridStyle,
  weekCalendarSlots: slots,
  weekCalendarLines: lines,
  weekCalendarHeight: height,
  weekCalendarBounds: bounds,
} = storeToRefs(store)
const { isTodayKey, entryStyle, formatEntryTimeRange, calendarEventStyle, openTaskDialog, openDayView } = store
</script>

<style scoped>
.calendar-entry__user {
  font-size: 0.75rem;
  font-weight: 700;
  margin-bottom: 2px;
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
  cursor: pointer;
}

.time-calendar__column-header--today {
  background: rgba(210, 153, 34, 0.12);
  border-radius: 10px 10px 0 0;
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

.time-calendar__column--today {
  background: linear-gradient(to bottom, rgba(210, 153, 34, 0.12), rgba(210, 153, 34, 0.04));
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

@media (max-width: 960px) {
  .time-calendar__header,
  .time-calendar__body {
    min-width: 720px;
  }
}
</style>