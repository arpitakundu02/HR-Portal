/**
 * components/common/Badge.js
 * Status badge with automatic colour mapping.
 */
const STATUS_CLASS = {
  'Pending':     'badge-pending',
  'Approved':    'badge-approved',
  'Rejected':    'badge-rejected',
  'Completed':   'badge-completed',
  'In Progress': 'badge-in-progress',
  'Admin':       'badge-admin',
  'Employee':    'badge-employee',
  'Active':      'badge-active',
  'Inactive':    'badge-inactive',
  'APL':         'badge-apl',
  'WFH':         'badge-wfh',
};

export default function Badge({ status }) {
  const cls = STATUS_CLASS[status] || 'badge-pending';
  return <span className={`badge ${cls}`}>{status}</span>;
}
