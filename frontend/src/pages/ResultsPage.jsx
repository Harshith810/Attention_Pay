import SecurityMap from '../components/location/SecurityMap';
import TransactionResultCard from '../components/results/TransactionResultCard';
import ExplanationPanel from '../components/results/ExplanationPanel';
import FeatureContributionChart from '../components/results/FeatureContributionChart';
import LimeContributionView from '../components/results/LimeContributionView';
import { useApp } from '../app/AppProvider';

function XAISkippedCard({ type }) {
  return (
    <div className="result-panel xai-skipped-card">
      <div className="panel-heading"><div><span className="eyebrow">XAI · {type}</span><h3>Explanation not executed</h3></div><span className="status-badge blocked">SKIPPED</span></div>
      <p className="summary">The backend security layer blocked this transaction before TabTransformer execution, so no {type} explanation payload was generated.</p>
      <small className="interpretation-note">This panel is a visual representation of the actual processing path; no explanation values are invented.</small>
    </div>
  );
}

export default function ResultsPage() {
  const { state } = useApp();
  if (!state.processingResponse) {
    return <section className="empty-page"><div className="section-card"><span className="eyebrow">SECURITY RESULTS</span><h2>Results are not available yet</h2><p>Complete transaction processing to review the location, decision and explainability results.</p></div></section>;
  }

  const ai = Boolean(state.processingResponse.ai_executed);

  return (
    <>
      <section className="hero compact-page-hero" id="security-results">
        <div>
          <h1>Security decision & explainability.</h1>
          <p>Review the completed transaction analysis, location security, backend explanation and model-focused XAI from the same backend response.</p>
        </div>
        <div className={`result-page-status ${state.processingResponse.decision === 'BLOCK' ? 'danger' : 'success'}`}>
          <span>FINAL STATUS</span><strong>{state.processingResponse.decision === 'BLOCK' ? 'BLOCKED' : 'APPROVED'}</strong>
        </div>
      </section>

      <section className="results-page-grid" id="location-security">
        <div className="result-full-card section-card"><SecurityMap /></div>
        <TransactionResultCard />
        <ExplanationPanel />
        {ai ? <FeatureContributionChart /> : <XAISkippedCard type="SHAP" />}
        {ai ? <LimeContributionView /> : <XAISkippedCard type="LIME" />}
      </section>
    </>
  );
}
