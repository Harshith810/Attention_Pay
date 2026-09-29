import { useApp } from '../app/AppProvider';
import { processTransaction } from '../api/simulationApi';
import { resolvePipeline } from '../utils/pipelineResolver';

const PIPELINE_ANIMATION_MS = 5100;
const FINAL_DECISION_HOLD_MS = 2000;

const wait = (ms) => new Promise((resolve) => window.setTimeout(resolve, ms));

export function useTransactionProcessing() {
  const { state, dispatch } = useApp();

  return async () => {
    if (!state.transaction) return;

    const startedAt = Date.now();
    dispatch({ type: 'PROCESS_START' });

    try {
      const response = await processTransaction(
        state.transaction.transaction_id,
        state.stage2AccessToken,
      );

      // Layer-1 responses can arrive almost immediately. Keep the workflow
      // visible for the same presentation duration as the AI path. During
      // this period the UI must NOT guess the final check symbols.
      const remainingAnimation = Math.max(0, PIPELINE_ANIMATION_MS - (Date.now() - startedAt));
      await wait(remainingAnimation);

      // Only after the presentation wait do we reveal the real backend result.
      // This prevents a temporary green check from being shown and then
      // replaced by the actual blocked/skipped symbol.
      dispatch({
        type: 'PROCESS_RESULT',
        response,
        pipeline: resolvePipeline(response),
      });

      // Keep the completed, backend-resolved workflow visible for review before
      // moving to the Results page.
      await wait(FINAL_DECISION_HOLD_MS);
      dispatch({ type: 'NAVIGATE_PAGE', page: 'results' });

      return response;
    } catch (e) {
      if (e?.response?.status === 403) dispatch({ type: 'RESET_SESSION' });
      else dispatch({ type: 'PROCESS_ERROR', error: e?.response?.data?.detail?.message || e.message || 'Unable to process transaction.' });
      throw e;
    }
  };
}
