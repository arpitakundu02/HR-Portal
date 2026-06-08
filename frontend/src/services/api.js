/**
 * services/api.js
 * ---------------
 * Centralised Axios instance and all API call functions.
 * - Automatically attaches JWT Bearer token to every request.
 * - Automatically redirects to /login on 401 responses.
 * - All API functions are grouped by module and exported by name.
 */

import axios from 'axios';

// Base URL proxied to Flask via package.json "proxy" setting
const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

/* ---- Request Interceptor: Attach JWT ---- */
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('hr_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

/* ---- Response Interceptor: Handle 401 ---- */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      sessionStorage.removeItem('hr_token');
      sessionStorage.removeItem('hr_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

/* ================================================================
   AUTH
   ================================================================ */
export const loginUser  = (data)   => api.post('/auth/login', data);
export const getMe      = ()       => api.get('/auth/me');

/* ================================================================
   EMPLOYEES
   ================================================================ */
export const getEmployees   = (params)      => api.get('/employees/', { params });
export const getEmployee    = (id)          => api.get(`/employees/${id}`);
export const createEmployee = (data)        => api.post('/employees/', data);
export const updateEmployee = (id, data)    => api.put(`/employees/${id}`, data);
export const deleteEmployee = (id)          => api.delete(`/employees/${id}`);

export const uploadResume = (id, formData) =>
  api.post(`/employees/${id}/resume`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

/* ================================================================
   DEPARTMENTS
   ================================================================ */
export const getDepartments    = ()           => api.get('/departments/');
export const createDepartment  = (data)       => api.post('/departments/', data);
export const updateDepartment  = (id, data)   => api.put(`/departments/${id}`, data);
export const deleteDepartment  = (id)         => api.delete(`/departments/${id}`);

/* ================================================================
   LEAVES
   ================================================================ */
export const getLeaveBalances    = (params)       => api.get('/leaves/balances', { params });
export const assignLeaveBalance  = (data)         => api.post('/leaves/balances', data);
export const applyLeave          = (data)         => api.post('/leaves/apply', data);
export const getLeaveHistory     = (params)       => api.get('/leaves/history', { params });
export const getLeaveRequests    = (params)       => api.get('/leaves/requests', { params });
export const actionLeaveRequest  = (id, status)   => api.post(`/leaves/requests/${id}/action`, { status });

/* ================================================================
   ATTENDANCE
   ================================================================ */
export const getTodayStatus       = ()        => api.get('/attendance/status');
export const checkIn              = (coords)  => api.post('/attendance/checkin', coords);
export const checkOut             = ()        => api.post('/attendance/checkout');
export const getAttendanceHistory = (params)  => api.get('/attendance/history', { params });
export const getOfficeSettings    = ()        => api.get('/attendance/settings');
export const updateOfficeSettings = (data)    => api.post('/attendance/settings', data);

/* ================================================================
   MEETINGS
   ================================================================ */
export const getMeetings    = (params)      => api.get('/meetings/', { params });
export const createMeeting  = (data)        => api.post('/meetings/', data);
export const updateMeeting  = (id, data)    => api.put(`/meetings/${id}`, data);
export const deleteMeeting  = (id)          => api.delete(`/meetings/${id}`);

/* ================================================================
   TASKS
   ================================================================ */
export const getTasks    = (params)      => api.get('/tasks/', { params });
export const createTask  = (data)        => api.post('/tasks/', data);
export const updateTask  = (id, data)    => api.put(`/tasks/${id}`, data);
export const deleteTask  = (id)          => api.delete(`/tasks/${id}`);

export default api;
