/**
 * components/common/Pagination.js
 * Page navigation component.
 */
export default function Pagination({ page, pages, onPageChange }) {
  if (pages <= 1) return null;

  const pageNums = [];
  for (let i = 1; i <= pages; i++) pageNums.push(i);

  return (
    <div className="pagination">
      <button
        className="pagination-btn"
        onClick={() => onPageChange(page - 1)}
        disabled={page === 1}
      >‹</button>

      {pageNums.map((n) => (
        <button
          key={n}
          className={`pagination-btn ${n === page ? 'active' : ''}`}
          onClick={() => onPageChange(n)}
        >{n}</button>
      ))}

      <button
        className="pagination-btn"
        onClick={() => onPageChange(page + 1)}
        disabled={page === pages}
      >›</button>

      <span className="pagination-info">Page {page} of {pages}</span>
    </div>
  );
}
