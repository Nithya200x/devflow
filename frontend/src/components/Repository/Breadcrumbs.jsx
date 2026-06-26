import { Link } from 'react-router-dom';
import { FiChevronRight } from 'react-icons/fi';

export function Breadcrumbs({ items }) {
  return (
    <nav className="breadcrumbs">
      {items.map((item, index) => (
        <span key={item.path || index} className="breadcrumb-item">
          {index > 0 && <FiChevronRight size={14} className="breadcrumb-sep" />}
          {item.path ? (
            <Link to={item.path}>{item.label}</Link>
          ) : (
            <span className="breadcrumb-current">{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}
