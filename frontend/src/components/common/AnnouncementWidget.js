import React, { useState, useEffect } from 'react';
import { getActiveAnnouncements } from '../../services/api';
import { MegaphoneIcon } from './Icons';
import { Link } from 'react-router-dom';

export default function AnnouncementWidget() {
  const [announcements, setAnnouncements] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await getActiveAnnouncements();
        setAnnouncements(res.data.slice(0, 3)); // Show up to 3 latest active announcements
      } catch (err) {
        console.error('Failed to load active announcements for dashboard:', err);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading || announcements.length === 0) return null;

  return (
    <div className="card" style={{ marginBottom: 24 }}>
      <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: 10 }}>
        <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 6, margin: 0 }}>
          <MegaphoneIcon style={{ width: 16, height: 16, color: 'var(--accent)' }} /> Active Announcements
        </div>
        <Link to="/announcements" style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent)', textDecoration: 'none' }}>
          View All &rarr;
        </Link>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 8 }}>
        {announcements.map((ann) => (
          <div 
            key={ann.id} 
            style={{ 
              padding: '12px 16px', 
              borderRadius: 8, 
              background: 'var(--bg-elevated)', 
              borderLeft: '4px solid var(--accent)' 
            }}
          >
            <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-primary)' }}>
              {ann.title}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
              {new Date(ann.created_at).toLocaleDateString()} · Posted by {ann.creator_name}
            </div>
            <div 
              style={{ 
                fontSize: 13, 
                color: 'var(--text-secondary)', 
                marginTop: 6, 
                lineHeight: 1.4,
                display: '-webkit-box', 
                WebkitLineClamp: 2, 
                WebkitBoxOrient: 'vertical', 
                overflow: 'hidden' 
              }}
            >
              {ann.content}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
