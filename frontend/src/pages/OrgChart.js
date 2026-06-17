import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { getHierarchy } from '../services/api';
import Spinner from '../components/common/Spinner';
import StatCard from '../components/common/StatCard';
import { useToast } from '../components/common/Toast';
import { UsersIcon, BuildingIcon, SearchIcon } from '../components/common/Icons';

export default function OrgChart() {
  const navigate = useNavigate();
  const toast = useToast();
  const [flatNodes, setFlatNodes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [deptFilter, setDeptFilter] = useState('');
  const [collapsedNodes, setCollapsedNodes] = useState(new Set());

  // Zoom and Pan States
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const dragStart = useRef({ x: 0, y: 0 });
  const containerRef = useRef(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getHierarchy();
      setFlatNodes(res.data);
    } catch (err) {
      toast.error('Failed to load organization hierarchy.');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Drag Handlers
  const handleMouseDown = (e) => {
    if (e.target.closest('button') || e.target.closest('.org-node-card')) return;
    setIsDragging(true);
    dragStart.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStart.current.x,
      y: e.clientY - dragStart.current.y
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Expand / Collapse Helpers
  const toggleCollapse = (nodeId) => {
    setCollapsedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  };

  // Helper to build hierarchy
  const buildNodeTree = (node, allNodes) => {
    const children = allNodes
      .filter((n) => n.manager_id === node.id)
      .map((n) => buildNodeTree(n, allNodes));
    return { ...node, children };
  };

  const getDepth = (node) => {
    if (!node.children || node.children.length === 0) return 1;
    return 1 + Math.max(...node.children.map(getDepth));
  };

  // 1. Calculate Summary Panel Metrics
  const totalEmployees = flatNodes.length;
  
  // A supervisor is any user who is set as manager_id for someone in the active list OR designated as is_line_manager
  const supervisorIds = new Set([
    ...flatNodes.map((n) => n.manager_id).filter((id) => id !== null),
    ...flatNodes.filter((n) => n.is_line_manager).map((n) => n.id)
  ]);
  const totalSupervisors = supervisorIds.size;

  const departmentNames = new Set(flatNodes.map((n) => n.department_name).filter(Boolean));
  const totalDepartments = departmentNames.size;

  // Build the complete tree to find the maximum depth
  const allRoots = flatNodes.filter(
    (item) => !item.manager_id || !flatNodes.some((p) => p.id === item.manager_id)
  );
  const maxDepth = allRoots.length > 0 
    ? Math.max(...allRoots.map((r) => getDepth(buildNodeTree(r, flatNodes)))) 
    : 0;

  // 2. Filter & Search Logic
  const matchesSearchAndFilter = (node) => {
    const query = search.trim().toLowerCase();
    const matchesSearch = !query || 
      node.name.toLowerCase().includes(query) || 
      node.employee_id.toLowerCase().includes(query);
    const matchesDept = !deptFilter || node.department_name === deptFilter;
    return matchesSearch && matchesDept;
  };

  // Retain parents for matching nodes
  const matchingNodes = flatNodes.filter(matchesSearchAndFilter);
  const visibleNodeIds = new Set();
  matchingNodes.forEach((node) => {
    let curr = node;
    while (curr) {
      visibleNodeIds.add(curr.id);
      const parentId = curr.manager_id;
      curr = parentId ? flatNodes.find((p) => p.id === parentId) : null;
    }
  });

  // 3. Build filtered tree
  const filteredRoots = allRoots
    .filter((r) => visibleNodeIds.has(r.id))
    .map((r) => buildNodeTree(r, flatNodes));

  // Recursive Tree Node Renderer
  const renderTreeNode = (node) => {
    const isCollapsed = collapsedNodes.has(node.id);
    const isMatch = matchesSearchAndFilter(node);
    const hasChildren = node.children && node.children.length > 0;

    // Prune children that aren't marked as visible
    const visibleChildren = node.children.filter((c) => visibleNodeIds.has(c.id));

    return (
      <div key={node.id} className="org-tree-node" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', margin: '0 10px' }}>
        {/* Node Card */}
        <div
          className={`card org-node-card ${isMatch ? 'org-node-match' : ''}`}
          onClick={(e) => {
            if (e.target.tagName !== 'BUTTON') {
              navigate(`/employees/${node.id}`);
            }
          }}
          style={{
            padding: 16,
            minWidth: 220,
            maxWidth: 260,
            border: isMatch ? '2px solid var(--accent)' : '1px solid var(--border)',
            boxShadow: isMatch ? '0 0 15px rgba(99, 102, 241, 0.25)' : 'none',
            borderRadius: 12,
            background: 'var(--bg-surface)',
            position: 'relative',
            textAlign: 'center',
            marginBottom: visibleChildren.length > 0 && !isCollapsed ? 20 : 0,
            transition: 'all 0.3s ease',
            cursor: 'pointer'
          }}
        >
          {/* Role Badge */}
          <div style={{ position: 'absolute', top: 8, right: 8 }}>
            <span
              className="badge"
              style={{
                fontSize: 10,
                backgroundColor: node.role === 'Admin' ? '#ef4444' : node.is_line_manager ? '#6366f1' : '#6b7280',
                color: '#fff',
                padding: '2px 6px',
                borderRadius: 4
              }}
            >
              {node.role === 'Admin' ? 'Admin' : node.is_line_manager ? 'Line Manager' : node.role}
            </span>
          </div>

          {/* Profile Photo */}
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 8, marginTop: 12 }}>
            {node.photo_url ? (
              <img src={node.photo_url} alt={node.name} style={{ width: 48, height: 48, borderRadius: '50%', objectFit: 'cover', border: '2px solid var(--border)' }} />
            ) : (
              <div style={{ width: 48, height: 48, borderRadius: '50%', backgroundColor: 'var(--bg-elevated)', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600, fontSize: 16, border: '2px solid var(--border)' }}>
                {node.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
              </div>
            )}
          </div>

          <div style={{ fontWeight: 800, fontSize: 15, color: 'var(--text-primary)' }}>
            {node.name}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
            ID: {node.employee_id}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 6, fontWeight: 600 }}>
            💼 {node.rank || 'Designation N/A'}
          </div>
          <div style={{ fontSize: 12, color: 'var(--accent)', marginTop: 4, fontWeight: 500 }}>
            🏢 {node.department_name || 'No Department'}
          </div>

          {node.manager_name && (
            <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 8, borderTop: '1px solid var(--border)', paddingTop: 6 }}>
              Reports to: <span style={{ fontWeight: 600 }}>{node.manager_name}</span>
            </div>
          )}

          {hasChildren && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleCollapse(node.id);
              }}
              className="btn btn-ghost btn-sm"
              style={{
                marginTop: 8,
                padding: '2px 8px',
                fontSize: 11,
                width: '100%',
                justifyContent: 'center',
                border: '1px solid var(--border)'
              }}
            >
              {isCollapsed ? `Expand (${visibleChildren.length})` : 'Collapse'}
            </button>
          )}
        </div>

        {/* Child branches */}
        {visibleChildren.length > 0 && !isCollapsed && (
          <div
            className="org-children-container"
            style={{
              display: 'flex',
              justifyContent: 'center',
              position: 'relative',
              paddingTop: 10,
              borderTop: '2px dashed var(--border)'
            }}
          >
            {visibleChildren.map(renderTreeNode)}
          </div>
        )}
      </div>
    );
  };

  if (loading) return <Spinner />;

  return (
    <div className="org-chart-page fade-in">
      <div className="page-header" style={{ marginBottom: 24 }}>
        <div>
          <h1 className="page-title">Organization Chart</h1>
          <p className="page-subtitle">Interactive hierarchy map of employee reporting relationships</p>
        </div>
      </div>

      {/* Summary Panel */}
      <div className="stats-grid" style={{ marginBottom: 24 }}>
        <StatCard icon={<UsersIcon />} value={totalEmployees} label="Total Employees" color="#10b981" />
        <StatCard icon={<UsersIcon />} value={totalSupervisors} label="Total Managers" color="#6366f1" />
        <StatCard icon={<BuildingIcon />} value={totalDepartments} label="Total Departments" color="#f59e0b" />
        <StatCard icon={<BuildingIcon />} value={maxDepth} label="Max Hierarchy Depth" color="#a78bfa" />
      </div>

      {/* Controls / Filter Bar */}
      <div className="search-filter-row" style={{ display: 'flex', gap: 16, marginBottom: 24, alignItems: 'center' }}>
        <div style={{ flex: 1, position: 'relative' }}>
          <input
            type="text"
            className="form-control"
            style={{ paddingLeft: 36 }}
            placeholder="Search by name or employee ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <SearchIcon style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
        </div>

        <div style={{ width: 220 }}>
          <select
            className="form-control"
            value={deptFilter}
            onChange={(e) => setDeptFilter(e.target.value)}
          >
            <option value="">All Departments</option>
            {Array.from(departmentNames).map((dept) => (
              <option key={dept} value={dept}>{dept}</option>
            ))}
          </select>
        </div>

        {(search || deptFilter) && (
          <button
            className="btn btn-secondary"
            onClick={() => {
              setSearch('');
              setDeptFilter('');
            }}
          >
            Reset Filters
          </button>
        )}
      </div>

      {/* Zoom and Pan controls */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 16, alignItems: 'center' }}>
        <span style={{ fontSize: 13, fontWeight: 600 }}>Chart View Controls:</span>
        <button className="btn btn-secondary btn-sm" onClick={() => setZoom(z => Math.max(0.4, z - 0.1))}>🔍- Zoom Out</button>
        <button className="btn btn-secondary btn-sm" onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }}>Reset View</button>
        <button className="btn btn-secondary btn-sm" onClick={() => setZoom(z => Math.min(1.8, z + 0.1))}>🔍+ Zoom In</button>
        <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 10 }}>Tip: Drag non-node areas of the box below to pan the chart.</span>
      </div>

      {/* Chart Trees Wrapper */}
      <div
        className="card"
        ref={containerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{
          padding: '40px 20px',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          minHeight: 500,
          background: 'var(--bg-surface)',
          cursor: isDragging ? 'grabbing' : 'grab',
          userSelect: 'none'
        }}
      >
        <div
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: 'top center',
            transition: isDragging ? 'none' : 'transform 0.15s ease-out',
            display: 'flex',
            gap: 40,
            justifyContent: 'center'
          }}
        >
          {filteredRoots.length === 0 ? (
            <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 48 }}>
              No hierarchy matching the search filters.
            </div>
          ) : (
            filteredRoots.map(renderTreeNode)
          )}
        </div>
      </div>
    </div>
  );
}
