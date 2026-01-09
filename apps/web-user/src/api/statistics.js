import http from './http'

export const getBillStats = (days = 7) => http.get('/statistics/bill', { params: { days } })

export const getSmokingStats = (days = 7) => http.get('/statistics/smoking', { params: { days } })

export const getScheduleStats = () => http.get('/statistics/schedule')
