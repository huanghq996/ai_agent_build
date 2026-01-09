import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('user_token') || '',
    user: null
  }),
  getters: {
    isLoggedIn: (state) => !!state.token
  },
  actions: {
    setToken(token) {
      this.token = token
      localStorage.setItem('user_token', token)
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('user_token')
    }
  }
})
