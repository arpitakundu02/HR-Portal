import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/common/Toast';
import Spinner from '../components/common/Spinner';
import Modal from '../components/common/Modal';
import Badge from '../components/common/Badge';
import {
  getPolicies,
  createPolicy,
  updatePolicy,
  deletePolicy,
  getPolicyHistory
} from '../services/api';
import {
  DocumentTextIcon,
  DownloadIcon,
  PlusIcon,
  EditIcon,
  TrashIcon,
  SearchIcon,
  ClockIcon,
  UploadIcon
} from '../components/common/Icons';

const CATEGORIES = [
  "Leave Policy",
  "Attendance Policy",
  "WFH Policy",
  "Comp-Off Policy",
  "Code of Conduct",
  "Security Guidelines",
  "Employee Handbook"
];

export default function Policies() {
  const { isAdmin } = useAuth();
  const toast = useToast();

  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");

  // CRUD Modals
  const [showFormModal, setShowFormModal] = useState(false);
  const [editTarget, setEditTarget] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(null);
  const [formLoading, setFormLoading] = useState(false);

  // Form states
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("Leave Policy");
  const [file, setFile] = useState(null);

  // Version History Modal
  const [showHistoryModal, setShowHistoryModal] = useState(null);
  const [historyList, setHistoryList] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const loadPolicies = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getPolicies();
      setPolicies(res.data || []);
    } catch {
      toast.error("Failed to load policies & handbook.");
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadPolicies();
  }, [loadPolicies]);

  const openCreateModal = () => {
    setEditTarget(null);
    setTitle("");
    setDescription("");
    setCategory("Leave Policy");
    setFile(null);
    setShowFormModal(true);
  };

  const openEditModal = (p) => {
    setEditTarget(p);
    setTitle(p.title);
    setDescription(p.description);
    setCategory(p.category);
    setFile(null);
    setShowFormModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !description.trim()) {
      toast.error("Please fill in title and description.");
      return;
    }

    const formData = new FormData();
    formData.append("title", title.trim());
    formData.append("description", description.trim());
    formData.append("category", category);
    if (file) {
      formData.append("attachment", file);
    }

    setFormLoading(true);
    try {
      if (editTarget) {
        await updatePolicy(editTarget.id, formData);
        toast.success("Policy updated to a new version.");
      } else {
        await createPolicy(formData);
        toast.success("Policy created successfully.");
      }
      setShowFormModal(false);
      loadPolicies();
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to save policy.");
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!showDeleteModal) return;
    try {
      await deletePolicy(showDeleteModal.id);
      toast.success("Policy deleted successfully.");
      setShowDeleteModal(null);
      loadPolicies();
    } catch {
      toast.error("Failed to delete policy.");
    }
  };

  const viewHistory = async (policy) => {
    setShowHistoryModal(policy);
    setHistoryLoading(true);
    setHistoryList([]);
    try {
      const res = await getPolicyHistory(policy.policy_group_id);
      setHistoryList(res.data || []);
    } catch {
      toast.error("Failed to load version history.");
    } finally {
      setHistoryLoading(false);
    }
  };

  const filteredPolicies = policies.filter((p) => {
    const matchesCategory = selectedCategory === "All" || p.category === selectedCategory;
    const matchesSearch =
      p.title.toLowerCase().includes(search.toLowerCase()) ||
      p.description.toLowerCase().includes(search.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="fade-in" style={{ paddingBottom: 40 }}>
      {/* Page Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 24, fontWeight: 800 }}>
            <DocumentTextIcon style={{ width: 28, height: 28 }} /> Policies & Handbook
          </h2>
          <p style={{ color: 'var(--text-secondary)', marginTop: 4 }}>Access official company guidelines, standard procedures, and compliance handbooks.</p>
        </div>
        {isAdmin && (
          <button className="btn btn-primary" onClick={openCreateModal}>
            <PlusIcon style={{ marginRight: 6 }} /> Create Policy
          </button>
        )}
      </div>

      {/* Filters card */}
      <div className="card" style={{ padding: 16, marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
          <div className="search-input-wrapper" style={{ flex: 1, minWidth: 260, position: 'relative' }}>
            <span style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}>
              <SearchIcon style={{ width: 16, height: 16 }} />
            </span>
            <input
              type="text"
              className="form-control"
              placeholder="Search policies by title or content..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: 36, width: '100%' }}
            />
          </div>
          <select
            className="form-control"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            style={{ width: 220 }}
          >
            <option value="All">All Categories</option>
            {CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Grid of Policies */}
      {loading ? (
        <Spinner />
      ) : filteredPolicies.length === 0 ? (
        <div className="card" style={{ padding: 40, textAlign: 'center', color: 'var(--text-secondary)' }}>
          No policies found matching the filters.
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 20 }}>
          {filteredPolicies.map((p) => (
            <div key={p.id} className="card" style={{ display: 'flex', flexDirection: 'column', height: '100%', justifyContent: 'space-between', padding: 24 }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                  <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: 'var(--accent-light)', letterSpacing: '0.05em' }}>
                    {p.category}
                  </span>
                  <Badge status="Active" text={`v${p.version}`} />
                </div>
                <h3 style={{ fontSize: 18, fontWeight: 700, margin: '0 0 8px 0', color: 'var(--text-primary)' }}>{p.title}</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: 13, display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden', textOverflow: 'ellipsis', marginBottom: 16, minHeight: 60, lineHeight: 1.5 }}>
                  {p.description}
                </p>
              </div>

              <div>
                {/* Meta details */}
                <div style={{ borderTop: '1px solid var(--border)', paddingTop: 12, marginBottom: 16, fontSize: 11, color: 'var(--text-muted)' }}>
                  <div>Updated By: <strong style={{ color: 'var(--text-secondary)' }}>{p.updated_by_name}</strong></div>
                  <div style={{ marginTop: 2 }}>Updated On: {new Date(p.updated_at).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</div>
                </div>

                {/* Actions */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    {p.attachment_url ? (
                      <a href={p.attachment_url} target="_blank" rel="noreferrer" className="btn btn-secondary btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                        <DownloadIcon style={{ width: 14, height: 14 }} /> Download PDF
                      </a>
                    ) : (
                      <span style={{ fontSize: 12, color: 'var(--text-muted)', italic: 'true' }}>No PDF attachment</span>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    {isAdmin && (
                      <>
                        <button className="btn btn-ghost btn-sm" onClick={() => viewHistory(p)} title="Version History">
                          <ClockIcon style={{ width: 16, height: 16 }} />
                        </button>
                        <button className="btn btn-ghost btn-sm" onClick={() => openEditModal(p)} title="Edit Policy">
                          <EditIcon style={{ width: 16, height: 16 }} />
                        </button>
                        <button className="btn btn-danger btn-sm" onClick={() => setShowDeleteModal(p)} title="Delete Policy">
                          <TrashIcon style={{ width: 14, height: 14 }} />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create/Edit Form Modal */}
      {showFormModal && (
        <Modal isOpen={true} onClose={() => setShowFormModal(false)} title={editTarget ? "Edit Policy / New Version" : "Create New Policy"}>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Category <span className="form-required">*</span></label>
              <select className="form-control" value={category} onChange={(e) => setCategory(e.target.value)}>
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Policy Title <span className="form-required">*</span></label>
              <input
                type="text"
                className="form-control"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Employee WFH Policy 2026"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Description <span className="form-required">*</span></label>
              <textarea
                className="form-control"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Write the policy text or brief summary..."
                required
                style={{ minHeight: 120 }}
              />
            </div>

            <div className="form-group">
              <label className="form-label">PDF Attachment {editTarget && "(Leave empty to keep existing)"}</label>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                <input
                  type="file"
                  id="policy-pdf"
                  accept=".pdf"
                  style={{ display: 'none' }}
                  onChange={(e) => setFile(e.target.files[0])}
                />
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => document.getElementById('policy-pdf').click()}
                  style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
                >
                  <UploadIcon style={{ width: 16, height: 16 }} /> {file ? "Change File" : "Choose PDF"}
                </button>
                {file && <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{file.name}</span>}
              </div>
            </div>

            <div className="form-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setShowFormModal(false)}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={formLoading}>
                {formLoading ? "Saving..." : editTarget ? "Create New Version" : "Publish Policy"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <Modal isOpen={true} onClose={() => setShowDeleteModal(null)} title="Delete Policy">
          <p style={{ margin: '0 0 20px 0', color: 'var(--text-primary)' }}>
            Are you sure you want to delete policy <strong>{showDeleteModal.title}</strong>? This will permanently delete <strong>all version history</strong>.
          </p>
          <div className="form-actions">
            <button className="btn btn-secondary" onClick={() => setShowDeleteModal(null)}>Cancel</button>
            <button className="btn btn-danger" onClick={handleDelete}>Delete Permanently</button>
          </div>
        </Modal>
      )}

      {/* Version History Modal */}
      {showHistoryModal && (
        <Modal isOpen={true} onClose={() => setShowHistoryModal(null)} title={`Version History: ${showHistoryModal.title}`}>
          {historyLoading ? (
            <Spinner />
          ) : historyList.length === 0 ? (
            <p style={{ color: 'var(--text-muted)' }}>No historical logs found.</p>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Ver</th>
                    <th>Title</th>
                    <th>Last Updated By</th>
                    <th>Last Updated On</th>
                    <th>PDF</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {historyList.map((ver) => (
                    <tr key={ver.id}>
                      <td style={{ fontWeight: 700 }}>v{ver.version}</td>
                      <td>{ver.title}</td>
                      <td>{ver.updated_by_name}</td>
                      <td>{new Date(ver.updated_at).toLocaleString('en-IN')}</td>
                      <td>
                        {ver.attachment_url ? (
                          <a href={ver.attachment_url} target="_blank" rel="noreferrer" className="btn btn-secondary btn-sm" style={{ padding: '4px 8px' }}>
                            View
                          </a>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td>
                        <Badge
                          status={ver.is_latest ? "Active" : "Rejected"}
                          text={ver.is_latest ? "Latest" : "Archived"}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="form-actions">
            <button className="btn btn-secondary" onClick={() => setShowHistoryModal(null)}>Close</button>
          </div>
        </Modal>
      )}
    </div>
  );
}
