<template>
  <v-app>
    <v-app-bar color="primary" dark density="compact">
      <v-toolbar-title>Time Audit</v-toolbar-title>
    </v-app-bar>
    <v-main>
      <v-container class="py-6">
        <upload-audit />
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import UploadAudit from './components/UploadAudit.vue'
</script>
