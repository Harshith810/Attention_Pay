import Navbar from '../components/layout/Navbar';
import PageShell from '../components/layout/PageShell';
import SecuritySetupPage from './SecuritySetupPage';
import TransactionFlowPage from './TransactionFlowPage';
import ResultsPage from './ResultsPage';
import { useApp } from '../app/AppProvider';

export default function SecuritySessionPage() {
  const { state } = useApp();
  const stage1Blocked = state.stage1.status === 'blocked' || Boolean(state.stage1.response?.blocked);
  // Stage 1 is a hard security gate. Even if a stale/previous navigation state
  // exists, a blocked URL can only render the setup page.
  const page = stage1Blocked ? 'setup' : (state.currentPage || 'setup');

  return (
    <>
      <Navbar />
      <PageShell>
        {page === 'transaction' ? <TransactionFlowPage /> : page === 'results' ? <ResultsPage /> : <SecuritySetupPage />}
      </PageShell>
    </>
  );
}
