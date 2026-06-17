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
    if (error.response?.status === 401 && !error.config?.url?.includes('/auth/login')) {
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
export const getBadgeCounts = ()   => api.get('/auth/badge-counts');

/* ================================================================
   EMPLOYEES
   ================================================================ */
export const getEmployees   = (params)      => api.get('/employees/', { params });
export const getEmployeeStats = ()          => api.get('/employees/stats');
export const getEmployee    = (id)          => api.get(`/employees/${id}`);
export const createEmployee = (data)        => api.post('/employees/', data);
export const updateEmployee = (id, data)    => api.put(`/employees/${id}`, data);
export const deleteEmployee = (id)          => api.delete(`/employees/${id}`);

export const uploadResume = (id, formData) =>
  api.post(`/employees/${id}/resume`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

export const uploadPhoto = (id, formData) =>
  api.post(`/employees/${id}/photo`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

export const getEmployeeDashboardDetails = (id) => api.get(`/employees/${id}/dashboard-details`);
export const deletePhoto = (id) => api.delete(`/employees/${id}/photo`);

/* ================================================================
   DEPARTMENTS
   ================================================================ */
export const getDepartments    = ()           => api.get('/departments/');
export const getDepartmentDetails = (id)      => api.get(`/departments/${id}`);
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
export const getLeaveStats       = ()             => api.get('/leaves/stats');
export const actionLeaveRequest  = (id, status)   => api.post(`/leaves/requests/${id}/action`, { status });

/* ================================================================
   ATTENDANCE
   ================================================================ */
export const getTodayStatus       = ()        => api.get('/attendance/status');
export const checkIn              = (coords)  => api.post('/attendance/checkin', coords);
export const checkOut             = ()        => api.post('/attendance/checkout');
export const getAttendanceHistory = (params)  => api.get('/attendance/history', { params });
export const getAttendanceStats   = ()         => api.get('/attendance/stats');
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
export const getTaskStats = ()           => api.get('/tasks/stats');
export const createTask  = (data)        => api.post('/tasks/', data);
export const updateTask  = (id, data)    => api.put(`/tasks/${id}`, data);
export const deleteTask  = (id)          => api.delete(`/tasks/${id}`);

/* ================================================================
   ATTENDANCE REGULARIZATION
   ================================================================ */
export const getRegularizationHistory  = ()                     => api.get('/attendance/regularization/history');
export const createRegularizationRequest = (data)               => api.post('/attendance/regularization', data);
export const actionRegularizationRequest = (id, status, comment) => api.post(`/attendance/regularization/${id}/action`, { status, comment });

/* ================================================================
   HOLIDAYS
   ================================================================ */
export const getHolidays    = (params) => api.get('/holidays', { params });
export const createHoliday  = (data)   => api.post('/holidays', data);
export const updateHoliday  = (id, data) => api.put(`/holidays/${id}`, data);
export const deleteHoliday  = (id)     => api.delete(`/holidays/${id}`);

/* ================================================================
   NOTIFICATIONS
   ================================================================ */
export const getNotifications            = (params) => api.get('/notifications/', { params });
export const getNotificationsUnreadCount = ()       => api.get('/notifications/unread-count');
export const markNotificationRead        = (id)     => api.post(`/notifications/${id}/read`);
export const markAllNotificationsRead    = ()       => api.post('/notifications/read-all');

/* ================================================================
   ANNOUNCEMENTS
   ================================================================ */
export const getAnnouncements       = ()       => api.get('/announcements/');
export const getActiveAnnouncements = ()       => api.get('/announcements/active');
export const createAnnouncement     = (data)   => api.post('/announcements/', data);
export const updateAnnouncement     = (id, data) => api.put(`/announcements/${id}`, data);
export const deleteAnnouncement     = (id)     => api.delete(`/announcements/${id}`);

/* ================================================================
   WORK TRANSFERS / DELEGATIONS
   ================================================================ */
export const getWorkTransfers       = ()       => api.get('/work-transfers/');
export const createWorkTransfer     = (data)   => api.post('/work-transfers/', data);

/* ================================================================
   REGISTRATIONS
   ================================================================ */
export const registerEmployee           = (data)   => api.post('/registrations/register', data);
export const getRegistrationRequests    = ()       => api.get('/registrations/requests');
export const actionRegistrationRequest  = (id, data) => api.post(`/registrations/requests/${id}/action`, data);

/* ================================================================
   COMP-OFF
   ================================================================ */
export const applyCompOff         = (data)   => api.post('/comp-off/request', data);
export const getCompOffHistory    = ()       => api.get('/comp-off/history');
export const getCompOffBalance    = ()       => api.get('/comp-off/balance');
export const getAdminCompOffAll   = ()       => api.get('/comp-off/admin/all');

/* ================================================================
   APPROVALS (CENTRALIZED)
   ================================================================ */
export const getPendingApprovals  = ()       => api.get('/approvals/pending');
export const actionApproval       = (id, data) => api.post(`/approvals/${id}/action`, data);

/* ================================================================
   TIMESHEETS
   ================================================================ */
export const submitTimesheet    = (data)   => api.post('/timesheets', data);
export const getTimesheetHistory = ()       => api.get('/timesheets');
export const getTeamTimesheets   = (params) => api.get('/timesheets/team', { params });

/* ================================================================
   TEAM DASHBOARD
   ================================================================ */
export const getTeamDashboardMetadata = () => api.get('/team-dashboard/metadata');
export const getTeamDashboardStats    = () => api.get('/team-dashboard/stats');

/* ================================================================
   ORGANIZATION HIERARCHY
   ================================================================ */
export const getHierarchy = () => api.get('/hierarchy');

export const getTeamLeaves      = (params) => api.get('/leaves/team', { params });
export const getTeamAttendance  = (params) => api.get('/attendance/team', { params });
export const getDirectory       = (params) => api.get('/employees/directory', { params });

/* ================================================================
   POLICIES & HANDBOOK
   ================================================================ */
export const getPolicies = () => api.get('/policies/');
export const getPoliciesStats = () => api.get('/policies/stats');
export const getPolicyHistory = (groupId) => api.get(`/policies/${groupId}/history`);
export const createPolicy = (formData) => api.post('/policies/', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
});
export const updatePolicy = (id, formData) => api.put(`/policies/${id}`, formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
});
export const deletePolicy = (id) => api.delete(`/policies/${id}`);

export default api;

