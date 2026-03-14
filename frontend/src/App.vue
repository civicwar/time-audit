<template>
  <v-app>
    <v-app-bar color="primary" dark density="compact">
      <v-toolbar-title>Time Audit</v-toolbar-title>
      <v-spacer />
      <v-btn variant="text" href="/">Upload & Analyze</v-btn>
      <template v-if="session">
        <v-chip size="small" class="mr-3">{{ session.user.role }}</v-chip>
        <v-btn variant="text" href="/in">Sessions</v-btn>
        <v-btn v-if="session.user.role === 'Admin'" variant="text" href="/in/users">Users</v-btn>
        <v-btn variant="text" @click="logout">Logout</v-btn>
      </template>
      <v-btn v-else variant="text" href="/login">Login</v-btn>
    </v-app-bar>
    <v-main :class="{ 'centered-main': isCenteredRoute }">
      <v-container class="py-6" :class="{ 'centered-container': isCenteredRoute }">
        <div v-if="route.name === 'login'" class="centered-card-wrapper">
          <login-view @authenticated="onAuthenticated" />
        </div>
        <div v-else-if="route.name === 'upload'" class="public-upload-wrapper">
          <upload-audit />
        </div>
        <session-workspace v-else-if="route.name === 'sessions'" />
        <public-report-review
          v-else-if="route.name === 'public-report'"
          :report-path="route.reportPath"
          :user="route.user"
        />
        <user-report-review
          v-else-if="route.name === 'private-report'"
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
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import LoginView from './components/LoginView.vue'
import PublicReportReview from './components/PublicReportReview.vue'
import SessionWorkspace from './components/SessionWorkspace.vue'
import UploadAudit from './components/UploadAudit.vue'
import UserManagement from './components/UserManagement.vue'
import UserReportReview from './components/UserReportReview.vue'
import { clearSession, getStoredSession, saveSession } from './services/api'

const route = ref({
  name: 'upload',
  reportPath: '',
  user: '',
})
const session = ref(getStoredSession())
const isCenteredRoute = computed(() => route.value.name === 'upload' || route.value.name === 'login')

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
  const publicReportRouteMatch = pathname.match(/^\/reports\/([^/]+)\/reviews$/)
  const reportRouteMatch = pathname.match(/^\/in\/reports\/([^/]+)\/reviews$/)

  if (!session.value && pathname.startsWith('/in')) {
    navigate('/login')
    return
  }

  if (session.value && pathname === '/login') {
    navigate('/in')
    return
  }

  if (reportRouteMatch) {
    const params = new URLSearchParams(search)
    route.value = {
      name: 'report',
      name: 'private-report',
      reportPath: decodeURIComponent(reportRouteMatch[1] || ''),
      user: params.get('user') || '',
    }
    return
  }

  if (publicReportRouteMatch) {
    const params = new URLSearchParams(search)
    route.value = {
      name: 'report',
      name: 'public-report',
      reportPath: decodeURIComponent(publicReportRouteMatch[1] || ''),
      user: params.get('user') || '',
    }
    return
  }

  if (pathname === '/' || pathname === '') {
    route.value = {
      name: 'upload',
      reportPath: '',
      user: '',
    }
    return
  }

  if (pathname === '/login') {
    route.value = {
      name: 'login',
      reportPath: '',
      user: '',
    }
    return
  }

  if (pathname === '/in' || pathname === '/in/') {
    route.value = {
      name: 'sessions',
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
    name: 'upload',
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

<style scoped>
.centered-main {
  display: flex;
}

.centered-container {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 64px);
}

.centered-card-wrapper {
  width: 100%;
}

.public-upload-wrapper {
  width: min(100%, 960px);
}
</style>
