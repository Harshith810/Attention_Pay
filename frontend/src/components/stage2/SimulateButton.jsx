import { useApp } from '../../app/AppProvider';
import { useTransactionProcessing } from '../../hooks/useTransactionProcessing';

export default function SimulateButton() {
  const { state } = useApp();
  const process = useTransactionProcessing();
  if (!state.transaction) return null;

  const busy = state.transactionStatus === 'processing' || Boolean(state.processingResponse);

  return (
    <button
      className='primary-btn large'
      onClick={() => process().catch(() => {})}
      disabled={busy}
    >
      {state.transactionStatus === 'processing'
        ? 'Processing transaction…'
        : state.processingResponse
          ? 'Processing complete'
          : 'Process Transaction'}
    </button>
  );
}
