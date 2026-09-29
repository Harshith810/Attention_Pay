import URLInputForm from '../components/stage1/URLInputForm';
import URLProcessingAnimation from '../components/stage1/URLProcessingAnimation';
import PhishingResultCard from '../components/stage1/PhishingResultCard';
import ScenarioDeck from '../components/stage2/ScenarioDeck';
import { useApp } from '../app/AppProvider';

export default function SecuritySetupPage() {
  const { state } = useApp();
  const legitimate = state.stage1.status === 'completed' && !state.stage1.response?.blocked;

  return (
    <>
      <section className="hero session-header" id="security-setup">
        <div>
          <h1>Start with the payment URL.</h1>
          <p>AttentionPay verifies the destination first, then opens the controlled transaction-security simulation only when the URL is legitimate.</p>
        </div>
      </section>

      <section className="section-card" id="url-security">
        <div className="section-heading">
          <div><span className="eyebrow">STAGE 1</span><h2>URL Security</h2><p>Analyze the payment URL with the BERT phishing detector.</p></div>
        </div>
        <URLInputForm />
        <URLProcessingAnimation />
        <PhishingResultCard />
      </section>

      {legitimate && (
        <section className="section-card scenario-section" id="scenario-selector">
          <div className="section-heading">
            <div>
              <span className="eyebrow">STAGE 2</span>
              <h2>Choose a security scenario</h2>
              <p>Select how the controlled demo transaction should be retrieved. The backend remains the source of truth for every outcome.</p>
            </div>
          </div>
          <ScenarioDeck />
        </section>
      )}
    </>
  );
}
