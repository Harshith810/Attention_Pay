import { useApp } from '../../app/AppProvider';

const links = [
  ['setup', 'Payment Verification'],
  ['transaction', 'Transaction Flow'],
  ['results', 'Security Results'],
];

export default function Navbar() {
  const { state, dispatch } = useApp();
  const stage1Blocked = state.stage1.status === 'blocked' || Boolean(state.stage1.response?.blocked);
  const stage1Complete = state.stage1.status === 'completed' && !stage1Blocked;
  const canTransaction = stage1Complete && Boolean(state.transaction);
  const canResults = stage1Complete && Boolean(state.processingResponse);
  const canNavigate = (page) => {
    if (stage1Blocked) return page === 'setup';
    return page === 'setup' || (page === 'transaction' && canTransaction) || (page === 'results' && canResults);
  };

  return (
    <nav className="navbar">
      <div className="nav-inner">
        <button className="brand-mark brand-button" onClick={() => dispatch({type:'NAVIGATE_PAGE', page:'setup'})} aria-label="Go to Payment Verification">
          <span className="brand-dot"/>AttentionPay
        </button>
        <div className="nav-links" aria-label="Security session navigation">
          {links.map(([page, label]) => (
            <button
              key={page}
              className={`nav-link ${state.currentPage === page ? 'active' : ''}`}
              onClick={() => dispatch({type:'NAVIGATE_PAGE', page})}
              disabled={!canNavigate(page)}
            >{label}</button>
          ))}
        </div>
        <div className="nav-actions">
          <div className="nav-session"><span className="status-dot"/>{stage1Blocked ? 'URL blocked' : state.processingResponse ? 'Session complete' : 'Security session active'}</div>
          <button className="ghost-btn" onClick={() => dispatch({type:'RESET_SESSION'})}>New session</button>
        </div>
      </div>
    </nav>
  );
}
