import Navbar from '../components/layout/Navbar';
import PageShell from '../components/layout/PageShell';

import SecuritySetupPage from './SecuritySetupPage';
import TransactionFlowPage from './TransactionFlowPage';
import ResultsPage from './ResultsPage';
import HowItWorksPage from './HowItWorksPage';

import { useApp } from '../app/AppProvider';

export default function SecuritySessionPage() {
  const { state } = useApp();

  const stage1Blocked =
    state.stage1.status === 'blocked' ||
    Boolean(state.stage1.response?.blocked);

  // How It Works is informational and can always be viewed.
  if (state.currentPage === 'how-it-works') {
    return (
      <>
        <Navbar />

        <PageShell>
          <HowItWorksPage />
        </PageShell>
      </>
    );
  }

  // Stage 1 remains a hard security gate for the actual transaction flow.
  const page = stage1Blocked
    ? 'setup'
    : state.currentPage || 'setup';

  return (
    <>
      <Navbar />

      <PageShell>
        {page === 'transaction' ? (
          <TransactionFlowPage />
        ) : page === 'results' ? (
          <ResultsPage />
        ) : (
          <SecuritySetupPage />
        )}
      </PageShell>
    </>
  );
}