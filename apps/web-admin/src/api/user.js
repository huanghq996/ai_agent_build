import http from './http'

export const getUsers = (page = 1, size = 10) =>
  http.get('/admin/users', { params: { page, size } })

export const getUser = (id) => http.get(`/admin/users/${id}`)

export const updateUserStatus = (id, status) =>
  http.put(`/admin/users/${id}/status`, null, { params: { status } })
