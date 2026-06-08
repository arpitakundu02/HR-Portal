/** components/common/Spinner.js */
export default function Spinner({ size = '' }) {
  return (
    <div className="spinner-wrapper">
      <div className={`spinner ${size ? `spinner-${size}` : ''}`} />
    </div>
  );
}
