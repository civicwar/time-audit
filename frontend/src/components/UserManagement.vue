<template>
  <v-card elevation="2" class="pa-4">
    <div class="d-flex align-center justify-space-between mb-4">
      <div>
        <h2 class="text-h6">User Management</h2>
        <div class="text-body-2 text-medium-emphasis">Admin-only access</div>
      </div>
      <v-btn color="primary" variant="text" href="/in">Back to Workspace</v-btn>
    </div>

    <v-alert v-if="error" type="error" variant="tonal" class="mb-4" :text="error" />
    <v-alert v-if="success" type="success" variant="tonal" class="mb-4" :text="success" />

    <v-card variant="outlined" class="pa-4 mb-6">
      <div class="text-subtitle-1 mb-3">Create User</div>
      <v-row>
        <v-col cols="12" md="3">
          <v-text-field v-model="createForm.username" label="Username" hide-details />
        </v-col>
        <v-col cols="12" md="3">
          <v-text-field v-model="createForm.full_name" label="Full name" hide-details />
        </v-col>
        <v-col cols="12" md="2">
          <v-select v-model="createForm.role" :items="roles" label="Role" hide-details />
        </v-col>
        <v-col cols="12" md="2">
          <v-text-field v-model="createForm.password" label="Password" type="password" hide-details />
        </v-col>
        <v-col cols="12" md="2" class="d-flex align-center">
          <v-switch v-model="createForm.is_active" label="Active" color="primary" hide-details inset />
        </v-col>
      </v-row>
      <v-btn color="primary" class="mt-4" :loading="creating" @click="createUser">Create user</v-btn>
    </v-card>

    <v-data-table :headers="headers" :items="users" item-value="id" density="comfortable">
      <template #item.role="{ item }">
        <v-select
          v-model="item.role"
          :items="roles"
          hide-details
          density="compact"
          variant="underlined"
          @update:model-value="markDirty(item.id)"
        />
      </template>

      <template #item.full_name="{ item }">
        <v-text-field
          v-model="item.full_name"
          hide-details
          density="compact"
          variant="underlined"
          @update:model-value="markDirty(item.id)"
        />
      </template>

      <template #item.is_active="{ item }">
        <v-switch
          v-model="item.is_active"
          color="primary"
          hide-details
          inset
          @update:model-value="markDirty(item.id)"
        />
      </template>

      <template #item.password="{ item }">
        <v-text-field
          v-model="passwordDrafts[item.id]"
          type="password"
          label="New password"
          hide-details
          density="compact"
          variant="underlined"
          @update:model-value="markDirty(item.id)"
        />
      </template>

      <template #item.actions="{ item }">
        <v-btn color="primary" variant="outlined" size="small" :disabled="!dirtyRows.has(item.id)" @click="saveUser(item)">
          Save
        </v-btn>
      </template>
    </v-data-table>
  </v-card>
</template>

<script setup>
import { onMounted, ref } from 'vue'

import api from '../services/api'

const roles = ['Admin', 'Developer', 'Reviewer']
const users = ref([])
const error = ref('')
const success = ref('')
const creating = ref(false)
const dirtyRows = ref(new Set())
const passwordDrafts = ref({})

const createForm = ref({
  username: '',
  full_name: '',
  password: '',
  role: 'Reviewer',
  is_active: true,
})

const headers = [
  { title: 'Username', key: 'username' },
  { title: 'Full Name', key: 'full_name' },
  { title: 'Role', key: 'role', sortable: false },
  { title: 'Active', key: 'is_active', sortable: false },
  { title: 'New Password', key: 'password', sortable: false },
  { title: 'Actions', key: 'actions', sortable: false },
]

const markDirty = (userId) => {
  dirtyRows.value = new Set([...dirtyRows.value, userId])
}

const clearMessages = () => {
  error.value = ''
  success.value = ''
}

const loadUsers = async () => {
  clearMessages()
  try {
    const { data } = await api.get('/api/in/users')
    users.value = data
  } catch (requestError) {
    error.value = requestError.response?.data?.detail || 'Could not load users.'
  }
}

const createUser = async () => {
  clearMessages()
  creating.value = true
  try {
    await api.post('/api/in/users', createForm.value)
    createForm.value = {
      username: '',
      full_name: '',
      password: '',
      role: 'Reviewer',
      is_active: true,
    }
    success.value = 'User created.'
    await loadUsers()
  } catch (requestError) {
    error.value = requestError.response?.data?.detail || 'Could not create user.'
  } finally {
    creating.value = false
  }
}

const saveUser = async (user) => {
  clearMessages()
  try {
    await api.patch(`/api/in/users/${user.id}`, {
      full_name: user.full_name,
      role: user.role,
      is_active: user.is_active,
      password: passwordDrafts.value[user.id] || null,
    })
    passwordDrafts.value[user.id] = ''
    const nextDirty = new Set(dirtyRows.value)
    nextDirty.delete(user.id)
    dirtyRows.value = nextDirty
    success.value = `Updated ${user.username}.`
    await loadUsers()
  } catch (requestError) {
    error.value = requestError.response?.data?.detail || 'Could not update user.'
  }
}

onMounted(loadUsers)
</script>