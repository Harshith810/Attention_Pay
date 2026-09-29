import { useEffect, useMemo, useState } from 'react';

const flowNodes = [
  {
    id: 'user',
    type: 'single',
    number: '00',
    title: 'User',
    subtitle: 'Payment journey begins',
    realTitle: 'User clicks a payment link',
    realText:
      'A real-world browser extension could observe the destination before the user enters payment information.',
    steps: [
      ['01', 'User clicks a payment link', 'The browser receives the destination.'],
      ['02', 'Browser opens the destination', 'The security layer gets the URL before payment continues.'],
      ['03', 'URL is handed to security', 'The destination becomes the input to Stage 1.'],
    ],
  },
  {
    id: 'bert',
    type: 'branch',
    number: '01',
    title: 'Stage 1: BERT Phishing Detection',
    subtitle: 'Verify the payment destination',
    realTitle: 'Browser extension → BERT verification',
    realText:
      'The extension intercepts the destination, tokenizes the URL, sends the tokens through BERT, and receives a phishing or legitimate prediction.',
    steps: [
      ['01', 'Browser extension captures the URL', 'The clicked destination is inspected before payment access is allowed.'],
      ['02', 'URL is tokenized', 'The URL is split into tokens that the transformer can process.'],
      ['03', 'BERT analyzes the tokens', 'The transformer evaluates patterns and contextual relationships in the URL.'],
      ['04', 'Prediction is produced', 'The model returns a phishing or legitimate classification with confidence.'],
      ['05', 'Security gate reacts', 'Phishing blocks the journey; legitimate continues to Stage 2.'],
    ],
  },
  {
    id: 'transaction',
    type: 'single',
    number: '02',
    title: 'Stage 2: Transaction Security',
    subtitle: 'Retrieve transaction context',
    realTitle: 'Payment API sends transaction context',
    realText:
      'In a real payment environment, the protected backend receives the transaction and the available security context from the payment system.',
    steps: [
      ['01', 'Payment request starts', 'The user initiates a payment after the destination passes Stage 1.'],
      ['02', 'Backend receives the request', 'The protected payment service becomes the next security boundary.'],
      ['03', 'Transaction context is retrieved', 'Amount, receiver, device, timing, location and related fields become available.'],
      ['04', 'Security pipeline starts', 'The transaction is passed to the deterministic Layer 1 checks.'],
    ],
  },
  {
    id: 'layer1',
    type: 'branch',
    number: '03',
    title: 'Layer 1 Security Checks',
    subtitle: 'Deterministic protection before AI',
    realTitle: 'Payment gateway performs rule checks',
    realText:
      'A production gateway can immediately verify request integrity and physically plausible transaction movement before spending compute on the AI layer.',
    steps: [
      ['01', 'API Route Integrity', 'Verify that the transaction reached the expected backend route.'],
      ['02', 'Impossible Travel', 'Compare previous and current locations with their timestamps.'],
      ['03', 'Decision gate', 'If either rule blocks, the transaction stops immediately.'],
      ['04', 'PASS path', 'Only transactions that pass Layer 1 continue to feature engineering.'],
    ],
  },
  {
    id: 'features',
    type: 'single',
    number: '04',
    title: 'Feature Engineering',
    subtitle: 'Build the model input',
    realTitle: 'Raw payment data becomes model features',
    realText:
      'A real fraud platform continuously transforms transaction history and current context into a consistent model-ready feature vector.',
    steps: [
      ['01', 'Collect raw transaction signals', 'Current transaction and relevant history are gathered.'],
      ['02', 'Transform values', 'Raw values are converted into the representations expected by the model.'],
      ['03', 'Build feature vector', 'The required feature columns are assembled in the trained schema order.'],
      ['04', 'Send to AI layer', 'The completed vector becomes the TabTransformer input.'],
    ],
  },
  {
    id: 'tab',
    type: 'single',
    number: '05',
    title: 'TabTransformer Fraud Detection',
    subtitle: 'Classify transaction behaviour',
    realTitle: 'Real-time fraud scoring service',
    realText:
      'A production fraud service can evaluate structured transaction features and return a risk classification or probability before authorization.',
    steps: [
      ['01', 'Feature vector enters model', 'Numerical and categorical transaction features are supplied to the model.'],
      ['02', 'Attention evaluates relationships', 'The transformer learns interactions between the structured features.'],
      ['03', 'Fraud probability is produced', 'The model calculates the probabilities for the transaction classes.'],
      ['04', 'Operating threshold is applied', 'The model output is converted into the fraud/legitimate decision used by the pipeline.'],
    ],
  },
  {
    id: 'xai',
    type: 'single',
    number: '06',
    title: 'Explainable AI',
    subtitle: 'SHAP / LIME',
    realTitle: 'Explain why the model reached its result',
    realText:
      'An authorized user, analyst or security system can inspect which model features contributed to an AI-layer decision.',
    steps: [
      ['01', 'Prediction is received', 'The explanation layer receives the completed model prediction.'],
      ['02', 'SHAP contribution view', 'Feature contributions are calculated around the model output.'],
      ['03', 'LIME local explanation', 'A second local explanation view shows influential feature behaviour.'],
      ['04', 'Explanation is attached', 'The result dashboard presents the prediction together with its supporting signals.'],
    ],
  },
  {
    id: 'decision',
    type: 'branch',
    number: '07',
    title: 'Result Dashboard',
    subtitle: 'Final security decision',
    realTitle: 'Payment authorization response',
    realText:
      'A real payment system could use the result to allow, decline, hold, step up authentication, or route the transaction for review.',
    steps: [
      ['01', 'Security result arrives', 'The backend returns the actual execution path and decision.'],
      ['02', 'Decision is displayed', 'The dashboard shows whether the transaction was blocked or allowed.'],
      ['03', 'Reason is shown', 'The relevant Layer 1 rule or AI explanation is presented.'],
      ['04', 'Payment system reacts', 'A real deployment could authorize, decline, hold or review the transaction.'],
    ],
  },
];

const futureExtensions = [
  {
    title: 'Browser Extension',
    text:
      'Move Stage 1 closer to the browser so payment destinations can be checked before users interact with them.',
  },
  {
    title: 'Payment Security Gateway',
    text:
      'Place the security pipeline in front of a payment-processing service so transactions are checked before downstream processing.',
  },
  {
    title: 'Financial-System Integration',
    text:
      'Connect the pipeline to live transaction streams, institution-specific signals and operational fraud systems.',
  },
];

function SimulationVisual({ nodeId, stepIndex }) {
  const common = `hw-sim-visual hw-sim-${nodeId}`;

  if (nodeId === 'user') {
    return (
      <div className={common}>
        <div className="hw-browser">
          <div className="hw-browser-bar">
            <span />
            <span />
            <span />
            <div>secure-payment.example</div>
          </div>
          <div className="hw-browser-body">
            <div className={`hw-link-card ${stepIndex >= 0 ? 'visible' : ''}`}>
              <span className="hw-link-icon">↗</span>
              <div>
                <strong>Pay securely</strong>
                <small>Click to continue to payment</small>
              </div>
              <b className="hw-click-cursor">⌁</b>
            </div>
            <div className="hw-browser-arrow">↓</div>
            <div className={`hw-extension-chip ${stepIndex >= 1 ? 'visible' : ''}`}>
              <i>✓</i> Security extension inspecting destination
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (nodeId === 'bert') {
    return (
      <div className={common}>
        <div className="hw-url-line">
          <span>https://</span>
          <b>secure-pay.example/login</b>
        </div>
        <div className="hw-token-row">
          {['https', '://', 'secure', '-', 'pay', '.', 'example', '/', 'login'].map(
            (token, i) => (
              <span
                key={`${token}-${i}`}
                className={i <= stepIndex + 1 ? 'token-show' : ''}
              >
                {token}
              </span>
            ),
          )}
        </div>
        <div className="hw-bert-box">
          <div className="hw-model-orbit">
            <span />
            <span />
            <span />
            <strong>BERT</strong>
          </div>
          <div className="hw-model-track">
            <i style={{ width: `${Math.min(100, 24 + stepIndex * 19)}%` }} />
          </div>
          <small>
            {stepIndex === 0
              ? 'capturing URL'
              : stepIndex === 1
                ? 'tokenizing URL'
                : stepIndex === 2
                  ? 'transformer analysis'
                  : stepIndex === 3
                    ? 'classification'
                    : 'security gate'}
          </small>
        </div>
        <div className="hw-prediction-row">
          <div className={stepIndex >= 3 ? 'prediction-active' : ''}>
            <span>LEGITIMATE</span>
            <b>{stepIndex >= 3 ? '98.7%' : '—'}</b>
          </div>
          <div className={stepIndex >= 3 ? 'prediction-risk' : ''}>
            <span>PHISHING</span>
            <b>{stepIndex >= 3 ? '1.3%' : '—'}</b>
          </div>
        </div>
        <div className={`hw-gate ${stepIndex >= 4 ? 'gate-open' : ''}`}>
          <span>{stepIndex >= 4 ? '✓' : '○'}</span>
          {stepIndex >= 4 ? 'LEGITIMATE → CONTINUE TO STAGE 2' : 'SECURITY GATE'}
        </div>
      </div>
    );
  }

  if (nodeId === 'transaction') {
    return (
      <div className={common}>
        <div className="hw-payment-card">
          <div className="hw-payment-header">
            <span>PAYMENT API</span>
            <b>₹ 4,850.00</b>
          </div>
          <div className="hw-payment-row"><span>Receiver</span><b>merchant@example</b></div>
          <div className="hw-payment-row"><span>Device</span><b>Known device</b></div>
          <div className="hw-payment-row"><span>Location</span><b>Bengaluru, IN</b></div>
        </div>
        <div className="hw-data-packets">
          {[0, 1, 2, 3].map((i) => (
            <i key={i} className={i <= stepIndex + 1 ? 'packet-on' : ''}>◆</i>
          ))}
        </div>
        <div className={`hw-server ${stepIndex >= 2 ? 'server-on' : ''}`}>
          <span>API</span>
          <strong>Transaction context</strong>
          <small>PostgreSQL → security pipeline</small>
        </div>
      </div>
    );
  }

  if (nodeId === 'layer1') {
    return (
      <div className={common}>
        <div className="hw-layer-grid">
          <div className={`hw-rule-card ${stepIndex >= 0 ? 'rule-on' : ''}`}>
            <span>01</span>
            <strong>API Route Integrity</strong>
            <small>expected endpoint</small>
            <b>{stepIndex >= 0 ? 'PASS' : 'CHECKING'}</b>
          </div>
          <div className={`hw-rule-card ${stepIndex >= 1 ? 'rule-on' : ''}`}>
            <span>02</span>
            <strong>Impossible Travel</strong>
            <small>location + time</small>
            <b>{stepIndex >= 1 ? 'PASS' : 'WAITING'}</b>
          </div>
        </div>
        <div className="hw-travel-line">
          <span className="travel-city">Previous</span>
          <i className={stepIndex >= 1 ? 'travel-on' : ''} />
          <span className="travel-dot" />
          <span className="travel-city">Current</span>
        </div>
        <div className={`hw-layer-decision ${stepIndex >= 2 ? 'decision-pass' : ''}`}>
          {stepIndex >= 2 ? '✓ PASS → FEATURE ENGINEERING' : 'SECURITY RULE GATE'}
        </div>
      </div>
    );
  }

  if (nodeId === 'features') {
    const features = ['amount', 'device', 'velocity', 'browser', 'history', 'risk'];
    return (
      <div className={common}>
        <div className="hw-feature-source">
          <span>RAW TRANSACTION</span>
          <i>→</i>
        </div>
        <div className="hw-feature-cloud">
          {features.map((feature, i) => (
            <span key={feature} className={i <= stepIndex + 1 ? 'feature-on' : ''}>
              {feature}
            </span>
          ))}
        </div>
        <div className="hw-feature-vector">
          <span>[</span>
          {features.map((_, i) => (
            <i key={i} className={i <= stepIndex + 1 ? 'vector-on' : ''} />
          ))}
          <span>]</span>
        </div>
        <small className="hw-feature-status">
          {stepIndex >= 3 ? 'MODEL-READY FEATURE VECTOR' : 'building feature vector…'}
        </small>
      </div>
    );
  }

  if (nodeId === 'tab') {
    return (
      <div className={common}>
        <div className="hw-transformer-input">
          {['amount', 'device', 'velocity', 'history'].map((item, i) => (
            <span key={item} className={i <= stepIndex ? 'input-on' : ''}>{item}</span>
          ))}
        </div>
        <div className="hw-attention-core">
          <div className="hw-attention-lines">
            <i />
            <i />
            <i />
            <i />
          </div>
          <strong>ATTENTION</strong>
          <small>feature interactions</small>
        </div>
        <div className="hw-model-output">
          <div>
            <span>FRAUD</span>
            <b style={{ height: `${stepIndex >= 2 ? 68 : 18}%` }} />
            <small>{stepIndex >= 2 ? '68%' : '—'}</small>
          </div>
          <div>
            <span>LEGITIMATE</span>
            <b style={{ height: `${stepIndex >= 2 ? 32 : 18}%` }} />
            <small>{stepIndex >= 2 ? '32%' : '—'}</small>
          </div>
        </div>
        <div className={`hw-threshold ${stepIndex >= 3 ? 'threshold-on' : ''}`}>
          {stepIndex >= 3 ? 'MODEL DECISION → FRAUD' : 'OPERATING THRESHOLD'}
        </div>
      </div>
    );
  }

  if (nodeId === 'xai') {
    const bars = [
      ['velocity', 82],
      ['device_changed', 64],
      ['amount', 49],
      ['history', 31],
      ['browser', 18],
    ];
    return (
      <div className={common}>
        <div className="hw-xai-header">
          <span className={stepIndex >= 1 ? 'xai-active' : ''}>SHAP</span>
          <i>+</i>
          <span className={stepIndex >= 2 ? 'xai-active' : ''}>LIME</span>
        </div>
        <div className="hw-xai-bars">
          {bars.map(([label, width], i) => (
            <div key={label}>
              <span>{label}</span>
              <i>
                <b style={{ width: stepIndex >= 1 && i <= stepIndex + 1 ? `${width}%` : '0%' }} />
              </i>
            </div>
          ))}
        </div>
        <div className={`hw-xai-callout ${stepIndex >= 3 ? 'xai-callout-on' : ''}`}>
          {stepIndex >= 3
            ? 'Top contributing signals attached to result'
            : 'calculating local explanation…'}
        </div>
      </div>
    );
  }

  if (nodeId === 'decision') {
    return (
      <div className={common}>
        <div className="hw-decision-gate">
          <div className="hw-gate-post" />
          <div className={`hw-gate-door ${stepIndex >= 2 ? 'door-open' : ''}`}>
            <span>{stepIndex >= 2 ? '✓' : '!'}</span>
          </div>
          <div className="hw-gate-road" />
        </div>
        <div className="hw-result-status">
          <span>{stepIndex >= 2 ? 'SECURITY RESULT' : 'PROCESSING RESULT'}</span>
          <strong>{stepIndex >= 2 ? 'TRANSACTION REVIEWED' : 'WAITING FOR DECISION'}</strong>
        </div>
        <div className={`hw-result-chip ${stepIndex >= 3 ? 'result-ready' : ''}`}>
          {stepIndex >= 3 ? 'DASHBOARD → RESULT + REASON' : 'preparing response…'}
        </div>
      </div>
    );
  }

  return null;
}

function SimulationModal({ node, onClose }) {
  const [stepIndex, setStepIndex] = useState(0);
  const [playing, setPlaying] = useState(true);

  useEffect(() => {
    setStepIndex(0);
    setPlaying(true);
  }, [node.id]);

  useEffect(() => {
    if (!playing) return undefined;

    const timer = window.setInterval(() => {
      setStepIndex((current) => {
        if (current >= node.steps.length - 1) {
          setPlaying(false);
          return current;
        }
        return current + 1;
      });
    }, 1700);

    return () => window.clearInterval(timer);
  }, [node.id, node.steps.length, playing]);

  const progress = ((stepIndex + 1) / node.steps.length) * 100;

  return (
    <div
      className="hw-modal-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section
        className="hw-simulation-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="hw-simulation-title"
      >
        <button type="button" className="hw-modal-close" onClick={onClose} aria-label="Close">
          ×
        </button>

        <div className="hw-modal-head">
          <div>
            <span>REAL-WORLD SIMULATION · STEP {node.number}</span>
            <h2 id="hw-simulation-title">{node.realTitle}</h2>
            <p>{node.realText}</p>
          </div>
          <div className="hw-modal-stage">
            <strong>{node.number}</strong>
            <small>SELECTED BLOCK</small>
          </div>
        </div>

        <div className="hw-simulation-progress">
          <i style={{ width: `${progress}%` }} />
        </div>

        <div className="hw-simulation-layout">
          <div className="hw-visual-shell">
            <div className="hw-visual-label">
              <span>LIVE CONCEPT ANIMATION</span>
              <b>{playing ? 'RUNNING' : 'COMPLETE'}</b>
            </div>
            <SimulationVisual nodeId={node.id} stepIndex={stepIndex} />
          </div>

          <div className="hw-step-panel">
            <div className="hw-step-label">
              <span>WHAT IS HAPPENING NOW</span>
              <strong>{stepIndex + 1}/{node.steps.length}</strong>
            </div>

            <div className="hw-current-step">
              <span>{node.steps[stepIndex][0]}</span>
              <div>
                <strong>{node.steps[stepIndex][1]}</strong>
                <p>{node.steps[stepIndex][2]}</p>
              </div>
            </div>

            <div className="hw-timeline">
              {node.steps.map(([number, title], index) => (
                <button
                  type="button"
                  key={number}
                  className={[
                    index === stepIndex ? 'current' : '',
                    index < stepIndex ? 'done' : '',
                  ].join(' ')}
                  onClick={() => {
                    setStepIndex(index);
                    setPlaying(false);
                  }}
                >
                  <span>{number}</span>
                  <strong>{title}</strong>
                </button>
              ))}
            </div>

            <div className="hw-modal-actions">
              <button
                type="button"
                className="hw-replay"
                onClick={() => {
                  setStepIndex(0);
                  setPlaying(true);
                }}
              >
                ↻ Replay
              </button>
              <button type="button" className="hw-close-action" onClick={onClose}>
                Back to flowchart
              </button>
            </div>
          </div>
        </div>

        <div className="hw-modal-note">
          <strong>Conceptual real-world view:</strong>
          This animation illustrates how the security concept could operate in
          a production environment. It does not claim that AttentionPay
          currently integrates with a live browser, bank, payment gateway, or
          financial institution.
        </div>
      </section>
    </div>
  );
}

function FlowConnector({ branch, active }) {
  if (branch) {
    return (
      <div className={`hw-branch-connector ${active ? 'active' : ''}`} aria-hidden="true">
        <div className="hw-branch-line" />
        <div className="hw-branch-left">
          <span>BLOCK</span>
          <b>↓</b>
          <em>BLOCKED</em>
        </div>
        <div className="hw-branch-right">
          <span>PASS</span>
          <b>↓</b>
        </div>
      </div>
    );
  }

  return (
    <div className={`hw-main-connector ${active ? 'active' : ''}`} aria-hidden="true">
      <span />
      <b>↓</b>
    </div>
  );
}

export default function HowItWorksPage() {
  const [selectedId, setSelectedId] = useState(null);
  const selectedNode = useMemo(
    () => flowNodes.find((node) => node.id === selectedId) || null,
    [selectedId],
  );

  return (
    <>
      <section className="hero compact-page-hero hw-flowchart-hero">
        <div>
          <span className="eyebrow">ATTENTIONPAY · SECURITY ARCHITECTURE</span>
          <h1>How AttentionPay protects a transaction.</h1>
          <p>
            Click any block in the flowchart. The rest of the architecture
            fades away and the selected block opens a step-by-step simulation
            of how that security stage could work in the real world.
          </p>
        </div>

        <div className="hw-flowchart-summary">
          <span>INTERACTIVE FLOW</span>
          <strong>USER → BERT → RULES → AI → XAI → RESULT</strong>
          <small>Click a block to run its simulation</small>
        </div>
      </section>

      <section className="section-card hw-flowchart-card">
        <div className="hw-flowchart-heading">
          <div>
            <span className="eyebrow">CLICK ANY BLOCK</span>
            <h2>AttentionPay security flowchart</h2>
            <p>
              The structure below mirrors the actual decision flow: phishing
              blocks at Stage 1, Layer 1 can block before AI, and only the
              passing path reaches the model and explainability stages.
            </p>
          </div>
        </div>

        <div className="hw-flowchart">
          <button
            type="button"
            className={`hw-node hw-node-user ${selectedId === 'user' ? 'selected' : ''}`}
            onClick={() => setSelectedId('user')}
          >
            <span className="hw-node-number">00</span>
            <strong>User</strong>
            <small>Payment journey begins</small>
          </button>

          <FlowConnector active={Boolean(selectedId)} />

          <button
            type="button"
            className={`hw-node ${selectedId === 'bert' ? 'selected' : ''}`}
            onClick={() => setSelectedId('bert')}
          >
            <span className="hw-node-number">01</span>
            <strong>Stage 1: BERT<br />Phishing Detection</strong>
            <small>Verify payment destination</small>
          </button>

          <FlowConnector branch active={selectedId === 'bert'} />

          <div className="hw-branch-result">
            <button
              type="button"
              className={`hw-branch-outcome danger ${selectedId === 'bert' ? 'related' : ''}`}
              onClick={() => setSelectedId('bert')}
            >
              <span>PHISHING</span>
              <b>↓</b>
              <strong>BLOCK</strong>
            </button>

            <button
              type="button"
              className={`hw-node hw-node-stage2 ${selectedId === 'transaction' ? 'selected' : ''}`}
              onClick={() => setSelectedId('transaction')}
            >
              <span className="hw-node-number">02</span>
              <strong>Stage 2: Transaction<br />Security</strong>
              <small>Retrieve transaction context</small>
            </button>
          </div>

          <FlowConnector active={selectedId === 'transaction' || selectedId === 'layer1'} />

          <button
            type="button"
            className={`hw-node hw-node-layer ${selectedId === 'layer1' ? 'selected' : ''}`}
            onClick={() => setSelectedId('layer1')}
          >
            <span className="hw-node-number">03</span>
            <strong>Layer 1 Security Checks</strong>
            <small>API Route Integrity · Impossible Travel</small>
          </button>

          <FlowConnector branch active={selectedId === 'layer1'} />

          <div className="hw-layer-outcomes">
            <button
              type="button"
              className={`hw-branch-outcome danger ${selectedId === 'layer1' ? 'related' : ''}`}
              onClick={() => setSelectedId('layer1')}
            >
              <span>BLOCK</span>
              <b>↓</b>
              <strong>BLOCKED</strong>
            </button>

            <div className="hw-pass-path">
              <span className="hw-pass-label">PASS</span>
              <b>↓</b>

              <button
                type="button"
                className={`hw-node hw-node-small ${selectedId === 'features' ? 'selected' : ''}`}
                onClick={() => setSelectedId('features')}
              >
                <span className="hw-node-number">04</span>
                <strong>Feature Engineering</strong>
              </button>

              <FlowConnector active={selectedId === 'features'} />

              <button
                type="button"
                className={`hw-node hw-node-small ${selectedId === 'tab' ? 'selected' : ''}`}
                onClick={() => setSelectedId('tab')}
              >
                <span className="hw-node-number">05</span>
                <strong>TabTransformer<br />Fraud Detection</strong>
              </button>

              <FlowConnector active={selectedId === 'tab'} />

              <button
                type="button"
                className={`hw-node hw-node-small ${selectedId === 'xai' ? 'selected' : ''}`}
                onClick={() => setSelectedId('xai')}
              >
                <span className="hw-node-number">06</span>
                <strong>Explainable AI</strong>
                <small>SHAP / LIME</small>
              </button>

              <FlowConnector active={selectedId === 'xai'} />

              <button
                type="button"
                className={`hw-node hw-node-small hw-node-result ${selectedId === 'decision' ? 'selected' : ''}`}
                onClick={() => setSelectedId('decision')}
              >
                <span className="hw-node-number">07</span>
                <strong>Result Dashboard</strong>
              </button>
            </div>
          </div>
        </div>

        <div className="hw-flowchart-footer">
          <span><i className="blue" /> Clickable security stage</span>
          <span><i className="red" /> Blocking path</span>
          <span><i className="green" /> Passing path</span>
          <span>Click outside the simulation to return here</span>
        </div>
      </section>

      <section className="section-card future-extensions-card">
        <div className="hw-flowchart-heading">
          <div>
            <span className="eyebrow">POTENTIAL FUTURE EXTENSIONS</span>
            <h2>Where this pipeline could go next.</h2>
            <p>
              These are future possibilities, not features currently
              implemented in the AttentionPay demo.
            </p>
          </div>
        </div>

        <div className="future-extension-grid">
          {futureExtensions.map((item, index) => (
            <article className="future-extension" key={item.title}>
              <span>0{index + 1}</span>
              <h3>{item.title}</h3>
              <p>{item.text}</p>
            </article>
          ))}
        </div>
      </section>

      {selectedNode && (
        <SimulationModal
          node={selectedNode}
          onClose={() => setSelectedId(null)}
        />
      )}
    </>
  );
}
