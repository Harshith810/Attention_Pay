import DemoTransactionPreview from '../components/stage2/DemoTransactionPreview';
import SimulateButton from '../components/stage2/SimulateButton';
import ProcessingPipeline from '../components/pipeline/ProcessingPipeline';
import { useApp } from '../app/AppProvider';

export default function TransactionFlowPage() {
  const { state } = useApp();
  if (!state.transaction) {
    return <section className="empty-page"><div className="section-card"><span className="eyebrow">TRANSACTION FLOW</span><h2>No transaction selected</h2><p>Return to Payment Verification and select a scenario to retrieve a demo transaction.</p></div></section>;
  }

  return (
    <>
      <section className="hero compact-page-hero">
        <div>
          <h1>Transaction security workflow.</h1>
          <p>The retrieved transaction stays visible beside the live security pipeline. Processing continues from the already-completed retrieval step.</p>
        </div>
        <div className="transaction-page-id"><span>TRANSACTION</span><strong>{state.transaction.transaction_id}</strong></div>
      </section>

      <section className="transaction-workflow-layout" id="transaction-flow">
        <aside className="transaction-side-card section-card">
          <div className="section-heading compact-heading">
            <div><span className="eyebrow">DEMO TRANSACTION</span><h2>Retrieved transaction</h2></div>
          </div>
          <DemoTransactionPreview />
          <div className="transaction-side-action"><SimulateButton /></div>
        </aside>

        <section className="pipeline-side-card section-card">
          <div className="section-heading compact-heading">
            <div><span className="eyebrow">SECURITY PIPELINE</span><h2>Actual processing path</h2><p>Each stage advances visually, while the completed state is resolved from the backend response.</p></div>
          </div>
          <ProcessingPipeline />
        </section>
      </section>
    </>
  );
}
