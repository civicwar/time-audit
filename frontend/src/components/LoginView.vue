<template>
  <v-row justify="center">
    <v-col cols="12" md="6" lg="4">
      <v-card elevation="3" class="pa-6">
        <div class="text-h5 mb-2">Sign In</div>
        <div class="text-body-2 text-medium-emphasis mb-6">
          Use one of the provisioned accounts to access the private area.
        </div>

        <v-alert
          v-if="error"
          type="error"
          variant="tonal"
          class="mb-4"
          :text="error"
        />

        <v-form @submit.prevent="submit">
          <v-text-field
            v-model="username"
            label="Username"
            autocomplete="username"
            :disabled="loading"
            required
          />
          <v-text-field
            v-model="password"
            label="Password"
            type="password"
            autocomplete="current-password"
            :disabled="loading"
            required
          />
          <v-btn type="submit" color="primary" block :loading="loading">Sign In</v-btn>
        </v-form>

        <v-divider class="my-4" />

        <div class="text-caption text-medium-emphasis">
          Default accounts: admin, developer, reviewer.
        </div>
      </v-card>
    </v-col>
  </v-row>
</template>

<script setup>
import { ref } from 'vue'

import api from '../services/api'

const emit = defineEmits(['authenticated'])

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const submit = async () => {
  loading.value = true
  error.value = ''
  try {
    const body = new URLSearchParams({
      username: username.value,
      password: password.value,
    })
    const { data } = await api.post('/api/auth/login', body, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    emit('authenticated', {
      token: data.access_token,
      user: data.user,
    })
  } catch (requestError) {
    error.value = requestError.response?.data?.detail || 'Could not sign in.'
  } finally {
    loading.value = false
  }
}
</script>