import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { aliases, mdi } from 'vuetify/iconsets/mdi'

const vuetify = createVuetify({
	components,
	directives,
	defaults: {
		VTextField: {
			variant: 'outlined',
		},
		VFileInput: {
			variant: 'outlined',
		},
		VSelect: {
			variant: 'outlined',
		},
		VCombobox: {
			variant: 'outlined',
		},
	},
	icons: {
		defaultSet: 'mdi',
		aliases,
		sets: {
			mdi,
		},
	},
	theme: {
		defaultTheme: 'dark',
	},
})

const pinia = createPinia()

createApp(App).use(pinia).use(vuetify).mount('#app')
