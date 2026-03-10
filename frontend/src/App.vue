<template>
  <v-app>
    <v-app-bar color="primary" dark density="compact">
      <v-toolbar-title>Time Audit</v-toolbar-title>
      <v-spacer />
      <template v-if="session">
        <v-chip size="small" class="mr-3">{{ session.user.role }}</v-chip>
        <v-btn variant="text" href="/in">Workspace</v-btn>
        <v-btn v-if="session.user.role === 'Admin'" variant="text" href="/in/users">Users</v-btn>
        <v-btn variant="text" @click="logout">Logout</v-btn>
      </template>
    </v-app-bar>
    <v-main>
      <v-container class="py-6">
        <login-view v-if="route.name === 'login'" @authenticated="onAuthenticated" />
        <upload-audit v-else-if="route.name === 'upload'" />
        <user-report-review
          v-else-if="route.name === 'report'"
          :report-path="route.reportPath"
          :user="route.user"
        />
        <user-management v-else-if="route.name === 'users'" />
        <v-alert v-else type="error" variant="tonal" text="Page not found." />
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import LoginView from './components/LoginView.vue'
import UploadAudit from './components/UploadAudit.vue'
import UserManagement from './components/UserManagement.vue'
import UserReportReview from './components/UserReportReview.vue'
import { clearSession, getStoredSession, saveSession } from './services/api'

const route = ref({
  name: 'login',
  reportPath: '',
  user: '',
})
const session = ref(getStoredSession())

const navigate = (path) => {
  if (window.location.pathname === path) {
    updateRouteFromLocation()
    return
  }
  window.history.pushState({}, '', path)
  updateRouteFromLocation()
}

const updateRouteFromLocation = () => {
  const { pathname, search } = window.location
  const reportRouteMatch = pathname.match(/^\/in\/reports\/([^/]+)\/reviews$/)

  if (!session.value && pathname.startsWith('/in')) {
    navigate('/')
    return
  }

  if (session.value && pathname === '/') {
    navigate('/in')
    return
  }

  if (reportRouteMatch) {
    const params = new URLSearchParams(search)
    route.value = {
      name: 'report',
      reportPath: decodeURIComponent(reportRouteMatch[1] || ''),
      user: params.get('user') || '',
    }
    return
  }

  if (pathname === '/in' || pathname === '/in/') {
    route.value = {
      name: 'upload',
      reportPath: '',
      user: '',
    }
    return
  }

  if (pathname === '/in/users') {
    route.value = {
      name: 'users',
      reportPath: '',
      user: '',
    }
    return
  }

  route.value = {
    name: 'login',
    reportPath: '',
    user: '',
  }
}

const onAuthenticated = (nextSession) => {
  saveSession(nextSession)
  session.value = nextSession
  navigate('/in')
}

const logout = () => {
  clearSession()
  session.value = null
  navigate('/')
}

onMounted(() => {
  updateRouteFromLocation()
  window.addEventListener('popstate', updateRouteFromLocation)
})

onBeforeUnmount(() => {
  window.removeEventListener('popstate', updateRouteFromLocation)
})
</script>
