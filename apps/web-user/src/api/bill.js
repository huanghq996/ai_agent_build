import http from './http'

export const getBills = (page = 1, size = 20) =>
  http.get('/bills', { params: { page, size } })

export const createBill = (data) => http.post('/bills', data)

export const getCategories = () => http.get('/categories')
