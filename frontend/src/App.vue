<template>
  <v-app>
    <v-app-bar color="primary" dark density="compact">
      <v-toolbar-title>Time Audit</v-toolbar-title>
    </v-app-bar>
    <v-main>
      <v-container class="py-6">
        <upload-audit v-if="route.name === 'upload'" />
        <user-report-review
          v-else-if="route.name === 'report'"
          :report-path="route.reportPath"
          :user="route.user"
        />
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import UploadAudit from './components/UploadAudit.vue'
import UserReportReview from './components/UserReportReview.vue'

const route = ref({
  name: 'upload',
  reportPath: '',
  user: '',
})

const updateRouteFromHash = () => {
  const hash = window.location.hash || '#/'
  const reportRouteMatch = hash.match(/^#\/reports\/([^/?#]+)\/reviews(?:\?.*)?$/)
  if (reportRouteMatch) {
    route.value = {
      name: 'report',
      reportPath: decodeURIComponent(reportRouteMatch[1] || ''),
      user: '',
    }
    return
  }

  if (hash.startsWith('#/report/')) {
    const rest = hash.replace('#/report/', '')
    const [rawPath, queryString = ''] = rest.split('?')
    const params = new URLSearchParams(queryString)
    const [runDir] = decodeURIComponent(rawPath || '').split('/')
    route.value = {
      name: 'report',
      reportPath: runDir || '',
      user: params.get('user') || '',
    }
    return
  }

  route.value = {
    name: 'upload',
    reportPath: '',
    user: '',
  }
}

onMounted(() => {
  updateRouteFromHash()
  window.addEventListener('hashchange', updateRouteFromHash)
})

onBeforeUnmount(() => {
  window.removeEventListener('hashchange', updateRouteFromHash)
})
</script>
