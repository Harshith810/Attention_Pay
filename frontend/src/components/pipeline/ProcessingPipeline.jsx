import { useEffect, useMemo, useState } from 'react';
import { useApp } from '../../app/AppProvider';

const labels = [
  ['transactionRetrieved', 'Transaction Retrieved', 'Demo transaction loaded from PostgreSQL'],
  ['apiRouteIntegrity', 'API Route Integrity', 'Validating the requested backend route'],
  ['impossibleTravel', 'Impossible Travel', 'Checking location, time and travel speed'],
  ['featureEngineering', 'Feature Engineering', 'Preparing the canonical model feature vector'],
  ['tabTransformer', 'TabTransformer', 'Evaluating behavioural transaction risk'],
  ['explainability', 'SHAP / LIME', 'Generating model-focused feature explanations'],
  ['finalDecision', 'Final Decision', 'Resolving the transaction action'],
];

const activeMessages = [
  'Loading the transaction context…',
  'Checking API route integrity…',
  'Checking travel consistency…',
  'Engineering the model input…',
  'Running behavioural fraud detection…',
  'Building SHAP and LIME explanations…',
  'Resolving the final transaction decision…',
];

function iconFor(status) {
  if (status === 'passed' || status === 'completed' || status === 'approved') return '✓';
  if (status === 'blocked') return '!';
  if (status === 'skipped') return '—';
  if (status === 'processing') return '•••';
  return '';
}

export default function ProcessingPipeline() {
  const { state } = useApp();
  const isProcessing = state.transactionStatus === 'processing';
  const hasResult = Boolean(state.processingResponse);
  const [activeIndex, setActiveIndex] = useState(1);

  useEffect(() => {
    if (!isProcessing) {
      setActiveIndex(state.transaction ? 1 : 0);
      return;
    }

    setActiveIndex(1);
    const timer = window.setInterval(() => {
      setActiveIndex((current) => Math.min(current + 1, labels.length - 1));
    }, 850);
    return () => window.clearInterval(timer);
  }, [isProcessing, state.transaction]);

  const effectiveSteps = useMemo(() => {
    // Before the backend response arrives, only the retrieval step is a known
    // completed state. All other stages are presentation-only and therefore do
    // not receive green checks or final blocked/skipped symbols yet.
    if (isProcessing) {
      return labels.map(([key], index) => {
        if (index === 0 && state.transaction) return 'passed';
        if (index === activeIndex) return 'processing';
        return 'pending';
      });
    }

    return labels.map(([key]) => state.pipeline[key]);
  }, [activeIndex, isProcessing, state.pipeline, state.transaction]);

  const completedCount = hasResult
    ? effectiveSteps.filter((status) => ['passed', 'completed', 'approved'].includes(status)).length
    : isProcessing
      ? Math.max(1, Math.min(activeIndex, labels.length - 1))
      : effectiveSteps.filter((status) => ['passed', 'completed', 'approved'].includes(status)).length;
  const progress = hasResult ? 100 : Math.round((completedCount / labels.length) * 100);

  const blockedIndex = effectiveSteps.findIndex((status) => status === 'blocked');
  const focusIndex = isProcessing
    ? activeIndex
    : blockedIndex >= 0
      ? blockedIndex
      : Math.max(0, effectiveSteps.findIndex((status) => ['processing', 'pending'].includes(status)));
  const focus = labels[Math.max(0, focusIndex)];

  return (
    <div className={`workflow ${isProcessing ? 'workflow-live' : ''} ${hasResult ? 'workflow-complete' : ''}`} aria-live="polite">
      <div className="workflow-topbar">
        <div>
          <span className="workflow-kicker">LIVE SECURITY WORKFLOW</span>
          <h3>{isProcessing ? 'Processing transaction…' : hasResult ? 'Processing complete' : 'Ready for security processing'}</h3>
          <p>{isProcessing ? activeMessages[activeIndex] : hasResult ? 'Every displayed result below is resolved from the backend response.' : 'Start the transaction to move through the security controls in sequence.'}</p>
        </div>
        <div className="workflow-progress-wrap">
          <strong>{progress}%</strong>
          <div className="workflow-progress"><i style={{ width: `${progress}%` }} /></div>
          <span>{isProcessing ? `Step ${Math.min(activeIndex + 1, labels.length)} of ${labels.length}` : hasResult ? 'Backend response received' : 'Waiting to start'}</span>
        </div>
      </div>

      <div className="workflow-layout">
        <div className="workflow-rail">
          {labels.map(([key, label, description], index) => {
            const status = effectiveSteps[index];
            const isFocus = index === focusIndex;
            return (
              <div className={`workflow-step ${status} ${isFocus ? 'focus' : ''}`} key={key}>
                <div className="workflow-step-marker">
                  <span>{iconFor(status)}</span>
                </div>
                {index < labels.length - 1 && <div className="workflow-connector"><i /></div>}
                <div className="workflow-step-copy">
                  <div className="workflow-step-head">
                    <span className="workflow-step-number">0{index + 1}</span>
                    <strong>{label}</strong>
                    <em>{status === 'processing' ? 'RUNNING' : status === 'passed' || status === 'completed' || status === 'approved' ? 'DONE' : status === 'blocked' ? 'BLOCKED' : status === 'skipped' ? 'SKIPPED' : 'PENDING'}</em>
                  </div>
                  <span>{description}</span>
                </div>
              </div>
            );
          })}
        </div>

        <div className="workflow-focus-card">
          <span className="workflow-kicker">CURRENT WORKFLOW STAGE</span>
          <div className="workflow-focus-number">0{Math.max(0, focusIndex + 1)}</div>
          <h4>{focus?.[1]}</h4>
          <p>{isProcessing ? activeMessages[focusIndex] : focus?.[2]}</p>
          <div className="workflow-focus-line" />
          <div className="workflow-status-row">
            <span>Transaction</span>
            <strong>{state.transaction?.transaction_id || '—'}</strong>
          </div>
          <div className="workflow-status-row">
            <span>Execution mode</span>
            <strong>{isProcessing ? 'LIVE REQUEST' : hasResult ? 'BACKEND RESOLVED' : 'READY'}</strong>
          </div>
          {hasResult && <div className={`workflow-final-chip ${state.processingResponse?.decision === 'BLOCK' ? 'danger' : 'success'}`}>
            {state.processingResponse?.decision === 'BLOCK' ? 'Transaction blocked' : 'Transaction approved to continue'}
          </div>}
        </div>
      </div>
    </div>
  );
}
