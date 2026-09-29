export default function StatusBadge({status,label}){return <span className={`status-badge ${status}`}>{label||status}</span>}
