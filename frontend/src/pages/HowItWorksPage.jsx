import { useEffect, useState } from 'react';
import '../styles/howItWorks.css';

const FEATS = ['known_device_flag', 'device_changed_flag', 'device_type', 'browser_name', 'operating_system', 'transactions_last_1min', 'transactions_last_5min', 'transactions_last_10min', 'transaction_amount', 'previous_transaction_amount', 'session_risk_score'];

const NODES = {
  user: { n: '00', t: 'User', sub: 'Payment journey begins', title: 'A customer clicks a payment link', intro: 'In a real deployment a browser extension sits between the click and the payment page.', steps: [['Customer clicks the link', 'A link in an email, chat or website asks the customer to pay.'], ['Browser starts navigating', 'The extension pauses the navigation before the page loads.'], ['URL handed to security', 'Only the destination URL is passed to AttentionPay Stage 1.']] },
  bert: { n: '01', t: 'Stage 1: BERT', sub: 'Phishing detection', title: 'Extension verifies the destination with BERT', intro: 'Before any payment page loads, the URL is checked by the trained BERT classifier.', toggle: true, steps: [['Extension captures the URL', 'The destination is read from the paused navigation.'], ['URL is tokenized', 'The tokenizer splits the URL into sub-word tokens BERT understands.'], ['BERT analyses the tokens', 'Attention weighs each token in context; odd tokens stand out.'], ['Prediction is produced', 'Phishing and legitimate probabilities are returned.'], ['Security gate reacts', 'Legitimate: the page opens and Stage 2 unlocks. Phishing: the page is blocked and the tokens are highlighted.']] },
  transaction: { n: '02', t: 'Stage 2: Transaction', sub: 'Retrieve context', title: 'Payment API supplies transaction context', intro: 'A real bank or gateway already holds this data. We simulated it with PostgreSQL.', steps: [['Payment request starts', 'The customer confirms a payment in the app.'], ['Backend receives it', 'The protected payment API is the next security boundary.'], ['Context is retrieved', 'Amount, device, location, time and endpoint become available.'], ['Security pipeline starts', 'The transaction is handed to Layer 1.']] },
  layer1: { n: '03', t: 'Layer 1 Checks', sub: 'API Route · Impossible Travel', title: 'Gateway runs deterministic rules first', intro: 'Cheap, explainable rules run before spending compute on the AI model.', toggle: true, steps: [['API Route Integrity', 'Was the request sent to the expected payment endpoint?'], ['Impossible Travel', 'Distance between the previous and current location divided by elapsed time.'], ['Decision gate', 'Any failed rule stops the transaction immediately.'], ['Outcome', 'Pass: continue to feature engineering. Block: AI is skipped and the rule is explained.']] },
  features: { n: '04', t: 'Feature Engineering', sub: 'Build the model input', title: 'Raw payment data becomes 11 model features', intro: 'A fraud platform turns transaction history and context into a fixed-order vector.', steps: [['Collect raw signals', 'Current transaction plus recent history are gathered.'], ['Transform values', 'Categories are encoded and numbers scaled with the saved scaler.'], ['Build the vector', 'All 11 features are assembled in the exact training order.'], ['Send to AI layer', 'The vector becomes the TabTransformer input.']] },
  tab: { n: '05', t: 'TabTransformer', sub: 'Fraud detection', title: 'Real-time fraud scoring before authorization', intro: 'The model scores behaviour: is this transaction unusual for this context?', toggle: true, steps: [['Vector enters the model', '3 categorical and 8 numerical inputs are supplied.'], ['Attention links features', 'The transformer learns interactions, e.g. new device with high amount.'], ['Fraud probability', 'The model outputs a probability for the transaction.'], ['Threshold applied', 'Probability above the 0.332 operating threshold is classified as fraud.']] },
  xai: { n: '06', t: 'Explainable AI', sub: 'SHAP / LIME', title: 'Analysts see why the model decided', intro: 'Explanations help fraud teams and customers trust and challenge decisions.', toggle: true, steps: [['Prediction received', 'The explainer gets the exact input used for prediction.'], ['SHAP contributions', 'Each feature pushes the score towards fraud or legitimate.'], ['LIME local view', 'A second, local explanation confirms the main drivers.'], ['Explanation attached', 'The decision is stored with its supporting signals.']] },
  decision: { n: '07', t: 'Result Dashboard', sub: 'Final decision', title: 'The payment system acts on the result', intro: 'The decision travels back to the bank or gateway, which chooses the action.', toggle: true, steps: [['Result arrives', 'The backend returns decision, source and execution path.'], ['Decision is shown', 'Allowed or blocked, with the layer that decided.'], ['Reason is shown', 'Rule explanation or SHAP/LIME, whichever made the decision.'], ['Payment system reacts', 'Approve, step-up authentication, hold for review, or decline.']] },
};

function Lane({ actors, pos }) {
  return (
    <div className="hiw-lane">
      {actors.map(([icon, label], i) => (
        <div key={label} className={'hiw-actor' + (i <= pos ? ' on' : '')}><span>{icon}</span><small>{label}</small></div>
      ))}
      <i className="hiw-packet" style={{ left: `${((pos + 0.5) * 100) / actors.length}%` }} />
    </div>
  );
}

const GOOD_T = ['https', ':', '//', 'pay', '.', 'example', '.', 'com', '/', 'checkout'];
const BAD_T = ['https', ':', '//', 'secure', '-', 'paypa', '##1', '-', 'login', '.', 'xyz', '/', 'verify'];
const SUS = ['paypa', '##1', 'xyz', 'login'];

const SCENES = {
  user: (s) => (
    <>
      <Lane actors={[['🧑', 'Customer'], ['🌐', 'Browser'], ['🛡️', 'Extension']]} pos={s} />
      <div className="hiw-browser">
        <div className="hiw-bar">● ● ●&nbsp; payment-link.example</div>
        <div className={'hiw-link' + (s === 0 ? ' click' : '')}>Pay securely ↗<b className="hiw-cursor">➤</b></div>
        {s >= 1 && <div className="hiw-note">{s >= 2 ? '🛡️ URL sent to AttentionPay Stage 1' : '⏸ Navigation paused by extension'}</div>}
      </div>
    </>
  ),
  bert: (s, bad) => {
    const toks = bad ? BAD_T : GOOD_T;
    const url = bad ? 'https://secure-paypa1-login.xyz/verify' : 'https://pay.example.com/checkout';
    return (
      <>
        <Lane actors={[['🌐', 'Browser'], ['🛡️', 'Extension'], ['🧠', 'BERT']]} pos={s === 0 ? 0 : s === 1 ? 1 : 2} />
        {s < 1 ? <div className="hiw-url">{url}</div> : (
          <div className="hiw-tokens split">
            {toks.map((t, i) => (
              <span key={i} className={'hiw-tok' + (s >= 2 && bad && SUS.includes(t) ? ' sus' : '')} style={{ transitionDelay: `${i * 50}ms` }}>
                {t}{s >= 2 && <i style={{ height: 6 + ((i * 7) % 5) * 5 + (bad && SUS.includes(t) ? 16 : 0) }} />}
              </span>
            ))}
          </div>
        )}
        {s >= 3 && (
          <div className="hiw-two">
            <div className={'hiw-card' + (bad ? '' : ' ok')}><small>LEGITIMATE</small><b>{bad ? '3%' : '98%'}</b></div>
            <div className={'hiw-card' + (bad ? ' no' : '')}><small>PHISHING</small><b>{bad ? '97%' : '2%'}</b></div>
          </div>
        )}
        {s >= 4 && <div className={'hiw-banner ' + (bad ? 'no' : 'ok')}>{bad ? '⛔ Page blocked. Warning shown with highlighted tokens.' : '✓ Page opens. Stage 2 unlocked.'}</div>}
      </>
    );
  },
  transaction: (s) => (
    <>
      <Lane actors={[['📱', 'Payment app'], ['🏦', 'Payment API'], ['🧠', 'Fraud service']]} pos={[0, 1, 1, 2][s]} />
      <div className="hiw-chips">
        {['₹4,850', 'known device', 'Bengaluru', '14:32:05', '/pay/v1'].map((c, i) => <span key={c} className={s >= 2 ? 'on' : ''} style={{ transitionDelay: `${i * 90}ms` }}>{c}</span>)}
      </div>
      <div className={'hiw-banner ' + (s >= 3 ? 'ok' : '')}>{s >= 3 ? '→ Layer 1 security checks' : 'Waiting for transaction context…'}</div>
    </>
  ),
  layer1: (s, bad) => (
    <>
      <div className="hiw-two">
        <div className={'hiw-card' + (s >= 1 ? ' ok' : '')}><small>API ROUTE INTEGRITY</small><b>{s >= 1 ? 'PASS' : '…'}</b><em>/pay/v1 = /pay/v1</em></div>
        <div className={'hiw-card' + (s >= 2 ? (bad ? ' no' : ' ok') : '')}><small>IMPOSSIBLE TRAVEL</small><b>{s >= 2 ? (bad ? 'FAIL' : 'PASS') : s >= 1 ? '…' : ''}</b><em>{bad ? 'Bengaluru → London in 18 min ≈ 26,000 km/h' : 'Bengaluru → Bengaluru, 4 min'}</em></div>
      </div>
      <div className="hiw-route"><span>Previous</span><i className={s >= 1 ? 'go' + (bad ? ' far' : '') : ''} /><span>Current</span></div>
      {s >= 2 && <div className={'hiw-banner ' + (bad ? 'no' : 'ok')}>{bad ? '⛔ BLOCK. AI skipped, rule explanation returned.' : '✓ PASS → Feature Engineering'}</div>}
    </>
  ),
  features: (s) => {
    const c = [3, 7, 11, 11][s];
    return (
      <>
        <div className="hiw-raw">RAW TRANSACTION {s >= 1 && '→ encode + scale'}</div>
        <div className="hiw-feats">{FEATS.map((f, i) => <span key={f} className={i < c ? 'on' : ''}>{i + 1}. {f}</span>)}</div>
        <div className={'hiw-banner ' + (s >= 3 ? 'ok' : '')}>{s >= 3 ? '[ 11 features, fixed order ] → TabTransformer' : 'building feature vector…'}</div>
      </>
    );
  },
  tab: (s, bad) => {
    const p = bad ? 81 : 14;
    return (
      <>
        <div className="hiw-vec">{FEATS.map((f, i) => <i key={f} className={s >= 0 ? 'on' : ''} style={{ transitionDelay: `${i * 40}ms` }} />)}</div>
        <div className={'hiw-attn' + (s >= 1 ? ' on' : '')}><b>ATTENTION</b><small>feature ↔ feature interactions</small></div>
        <div className="hiw-meter">
          <div className="hiw-fill" style={{ width: s >= 2 ? `${p}%` : '0%' }} />
          <div className="hiw-mark" style={{ left: '33.2%' }}><small>0.332</small></div>
        </div>
        <div className="hiw-meter-l">Fraud probability {s >= 2 ? (p / 100).toFixed(2) : '—'} <em>(illustrative)</em></div>
        {s >= 3 && <div className={'hiw-banner ' + (bad ? 'no' : 'ok')}>{bad ? 'Above threshold → FRAUD' : 'Below threshold → LEGITIMATE'}</div>}
      </>
    );
  },
  xai: (s, bad) => {
    const rows = bad
      ? [['session_risk_score', 31], ['device_changed_flag', 22], ['transaction_amount', 18], ['known_device_flag', -6], ['device_type', -3]]
      : [['known_device_flag', -24], ['session_risk_score', -17], ['transaction_amount', 8], ['device_changed_flag', -6], ['device_type', 3]];
    return (
      <>
        <div className="hiw-xai-h"><span className={s >= 1 ? 'on' : ''}>SHAP</span><span className={s >= 2 ? 'on' : ''}>LIME</span></div>
        {rows.map(([f, v], i) => (
          <div className="hiw-xrow" key={f}>
            <small>{f}</small>
            <div><b className={v > 0 ? 'up' : 'dn'} style={{ width: s >= 1 ? Math.abs(v) * 1.6 : 0, [v > 0 ? 'left' : 'right']: '50%' }} /></div>
            <div><b className={v > 0 ? 'up' : 'dn'} style={{ width: s >= 2 ? Math.abs(v) * 1.3 : 0, [v > 0 ? 'left' : 'right']: '50%' }} /></div>
          </div>
        ))}
        <div className="hiw-legend">red pushes towards fraud · green towards legitimate · <em>illustrative</em></div>
        {s >= 3 && <div className="hiw-banner ok">Top signals attached to the decision record</div>}
      </>
    );
  },
  decision: (s, bad) => (
    <>
      <Lane actors={[['🛡️', 'AttentionPay'], ['🏦', 'Bank / gateway'], ['🧑', 'Customer']]} pos={[0, 0, 1, 2][s]} />
      <div className={'hiw-banner ' + (s >= 1 ? (bad ? 'no' : 'ok') : '')}>{s >= 1 ? (bad ? 'BLOCK' : 'CONTINUE') : 'waiting for decision…'}{s >= 2 && (bad ? ' · high fraud probability, top driver session_risk_score' : ' · checks passed, low fraud probability')}</div>
      <div className="hiw-acts">
        {[['Approve', !bad], ['Step-up auth', false], ['Hold for review', bad], ['Decline', bad]].map(([a, on]) => <span key={a} className={s >= 3 && on ? (bad ? 'no' : 'ok') : ''}>{a}</span>)}
      </div>
    </>
  ),
};

function Expanded({ id, rect, startBad, onClose }) {
  const node = NODES[id];
  const [phase, setPhase] = useState('from');
  const [s, setS] = useState(0);
  const [play, setPlay] = useState(true);
  const [bad, setBad] = useState(startBad);
  const last = node.steps.length - 1;

  useEffect(() => {
    const r = requestAnimationFrame(() => requestAnimationFrame(() => setPhase('open')));
    return () => cancelAnimationFrame(r);
  }, []);
  useEffect(() => {
    if (!play || phase !== 'open') return undefined;
    const t = setTimeout(() => (s < last ? setS(s + 1) : setPlay(false)), 2300);
    return () => clearTimeout(t);
  }, [s, play, phase, last]);
  const close = () => { setPhase('closing'); setTimeout(onClose, 450); };
  useEffect(() => {
    const k = (e) => e.key === 'Escape' && close();
    window.addEventListener('keydown', k);
    return () => window.removeEventListener('keydown', k);
  }, []);

  const vw = window.innerWidth, vh = window.innerHeight;
  const w = Math.min(900, Math.round(vw * 0.78)), h = Math.min(580, Math.round(vh * 0.72), vh - 110);
  const top = Math.max(88, Math.round((vh - h) / 2) + 24);
  const open = phase === 'open';
  const style = open ? { left: (vw - w) / 2, top, width: w, height: h } : { left: rect.left, top: rect.top, width: rect.width, height: rect.height };
  const replay = () => { setS(0); setPlay(true); };

  return (
    <>
      <div className={'hiw-scrim' + (open ? ' open' : '')} onMouseDown={close} />
      <section className={'hiw-card-x' + (open ? ' open' : '')} style={style} role="dialog" aria-modal="true" aria-label={node.title}>
        <div className="hiw-x-body">
          <header>
            <span className="hiw-num">{node.n}</span>
            <div><small>REAL-WORLD SIMULATION</small><h2>{node.title}</h2><p>{node.intro}</p></div>
            <button type="button" className="hiw-x" onClick={close} aria-label="Close">×</button>
          </header>
          <div className="hiw-prog"><i style={{ width: `${((s + 1) / node.steps.length) * 100}%` }} /></div>
          <div className="hiw-grid">
            <div className="hiw-scene">{SCENES[id](s, bad)}</div>
            <ol className="hiw-steps">
              {node.steps.map(([t, d], i) => (
                <li key={t} className={i === s ? 'cur' : i < s ? 'done' : ''}>
                  <button type="button" onClick={() => { setS(i); setPlay(false); }}>
                    <b>{i + 1}</b><span><strong>{t}</strong>{i === s && <em>{d}</em>}</span>
                  </button>
                </li>
              ))}
            </ol>
          </div>
          <footer>
            <button type="button" onClick={replay}>↻ Replay</button>
            {play ? <button type="button" onClick={() => setPlay(false)}>❚❚ Pause</button> : s < last && <button type="button" onClick={() => setPlay(true)}>▶ Play</button>}
            {node.toggle && <button type="button" className={bad ? 'tog bad' : 'tog'} onClick={() => { setBad(!bad); replay(); }}>{bad ? '⛔ Blocked case: switch to normal' : '✓ Normal case: show blocked case'}</button>}
            <small>Conceptual view. AttentionPay does not connect to a real bank, browser or payment gateway.</small>
          </footer>
        </div>
      </section>
    </>
  );
}


function Group({ tag, title, sub, real, children }) {
  return (
    <div className="hiw-group">
      <div className="hiw-zl"><small>{tag}</small><strong>{title}</strong><span>{sub}</span><em>Real world: {real}</em></div>
      {children}
    </div>
  );
}

const ROWS = [
  ['🔗', 'Payment URL', 'Form input', 'The user pastes a URL into the security page.', 'Extension / gateway', 'The link is intercepted automatically when the customer clicks it in a browser, email or chat.'],
  ['💳', 'Transaction source', 'Scenario selector', 'A scenario card picks a controlled transaction.', 'Live payment event', 'The bank, merchant or payment API sends the real payment request at authorization time.'],
  ['🗄️', 'Transaction data', 'PostgreSQL rows', 'Seeded demo_transactions table.', 'Live data + history', 'Streaming transaction store combined with the customer’s device, session and spending history.'],
  ['📍', 'Location and time', 'Stored coordinates', 'Fixed previous/current latitude, longitude and timestamps.', 'Real signals', 'IP geolocation, consented device location, and the bank’s record of the previous transaction.'],
  ['🛣️', 'API route check', 'Simulated fields', 'Expected and actual endpoint saved in the row.', 'Gateway metadata', 'The gateway verifies the actual request path, tokens and signatures of the call.'],
  ['🧠', 'Fraud scoring', 'FastAPI + saved model', 'TabTransformer trained offline on a 200,000-row dataset.', 'Scoring service', 'A low-latency model service that is monitored and retrained on confirmed fraud outcomes.'],
  ['🔍', 'Explanations', 'Result page', 'SHAP/LIME shown once on the dashboard.', 'Audit record', 'Stored with every decision so analysts, auditors and dispute teams can review why it happened.'],
  ['✅', 'Final action', 'Blocked / Approved', 'A status card on the dashboard.', 'Authorization response', 'Approve, decline, ask for step-up authentication such as an OTP, or hold for analyst review.'],
];

const SAME = [
  ['Same order of checks', 'URL first, deterministic rules next, AI only after both pass.'],
  ['Same feature contract', 'The 11 features keep the same order in training and inference.'],
  ['Same explanation logic', 'Rule blocks are explained by rules, AI decisions by SHAP/LIME.'],
];

const FUTURE = [
  ['Browser Extension', 'Move Stage 1 into the browser so destinations are checked before the user interacts.'],
  ['Payment Security Gateway', 'Place the pipeline in front of payment processing so every transaction is screened first.'],
  ['Financial-System Integration', 'Connect live transaction streams and institution signals to the fraud pipeline.'],
];

export default function HowItWorksPage() {
  const [sel, setSel] = useState(null);

  const Node = ({ id, small }) => {
    const n = NODES[id];
    return (
      <button type="button" className={'hiw-node' + (small ? ' small' : '') + (sel?.id === id ? ' lifted' : '')}
        onClick={(e) => setSel({ id, rect: e.currentTarget.getBoundingClientRect(), bad: false })}>
        <span className="hiw-num">{n.n}</span><strong>{n.t}</strong><small>{n.sub}</small>
      </button>
    );
  };
  const Arrow = () => <div className="hiw-arrow" aria-hidden="true"><i /></div>;
  const Blocked = ({ id, tag }) => (
    <button type="button" className="hiw-blocked" onClick={(e) => setSel({ id, rect: e.currentTarget.getBoundingClientRect(), bad: true })}>
      <small>{tag}</small><strong>⛔ BLOCK</strong><em>see it happen</em>
    </button>
  );
  const Branch = ({ id, bad, ok }) => (
    <div className="hiw-branch">
      <Blocked id={id} tag={bad} />
      <div className="hiw-okwrap"><Arrow /><span className="hiw-okl">{ok}</span></div>
    </div>
  );

  return (
    <div className="hiw">
      <section className="hiw-hero">
        <span className="hiw-eyebrow">ATTENTIONPAY · HOW IT WORKS</span>
        <h1>How AttentionPay would protect a real payment.</h1>
        <p>Click any block. The block expands, the rest of the flowchart fades back, and a step-by-step animation shows how that stage would work in the real world, from a customer clicking a link to the bank acting on the result.</p>
      </section>

      <section className="hiw-panel">
        <div className={'hiw-chart' + (sel ? ' dim' : '')}>
          <Group tag="STAGE 1" title="URL security" sub="Before the payment page opens" real="Browser extension or link scanner">
            <Node id="user" /><Arrow /><Node id="bert" />
            <Branch id="bert" bad="PHISHING" ok="LEGITIMATE" />
          </Group>
          <Group tag="STAGE 2 · LAYER 1" title="Transaction security" sub="When the customer pays" real="Payment gateway / API layer">
            <Node id="transaction" /><Arrow /><Node id="layer1" />
            <Branch id="layer1" bad="RULE FAILS" ok="RULES PASS" />
          </Group>
          <Group tag="STAGE 2 · LAYER 2" title="AI fraud detection" sub="Runs only when Layer 1 passes" real="Real-time fraud scoring service">
            <Node id="features" /><Arrow />
            <Node id="tab" /><Arrow />
            <Node id="xai" />
          </Group>
          <Arrow />
          <Group tag="OUTCOME" title="Final decision" sub="Result returns to the payment system" real="Bank / payment authorization">
            <Node id="decision" />
          </Group>
        </div>
        <div className="hiw-key"><span><i className="b" />Click a stage to expand it</span><span><i className="r" />Blocking path</span><span><i className="g" />Passing path</span></div>
      </section>

      <section className="hiw-panel">
        <span className="hiw-eyebrow">DEMO VS REAL WORLD</span>
        <h2>What changes outside the simulation?</h2>
        <p className="hiw-sub">The security logic stays the same. What changes is where the data comes from and where the pipeline plugs in.</p>
        <div className="hiw-cmp">
          <div className="hiw-cmp-head"><span /><span>IN THIS PROJECT (DEMO)</span><span /><span>IN A REAL DEPLOYMENT</span></div>
          {ROWS.map(([icon, name, dc, dt, rc, rt]) => (
            <div className="hiw-cmp-row" key={name}>
              <div className="hiw-cmp-k"><i>{icon}</i><strong>{name}</strong></div>
              <div className="hiw-cmp-d"><b>{dc}</b><span>{dt}</span></div>
              <div className="hiw-cmp-a">→</div>
              <div className="hiw-cmp-r"><b>{rc}</b><span>{rt}</span></div>
            </div>
          ))}
        </div>
        <div className="hiw-same">
          {SAME.map(([t, d]) => <div key={t}><strong>✓ {t}</strong><span>{d}</span></div>)}
        </div>
      </section>

      <section className="hiw-panel">
        <span className="hiw-eyebrow">POTENTIAL FUTURE EXTENSIONS</span>
        <h2>Where this pipeline could go next.</h2>
        <div className="hiw-future">{FUTURE.map(([t, d], i) => <article key={t}><span>0{i + 1}</span><h3>{t}</h3><p>{d}</p></article>)}</div>
      </section>

      {sel && <Expanded key={sel.id + sel.bad} id={sel.id} rect={sel.rect} startBad={sel.bad} onClose={() => setSel(null)} />}
    </div>
  );
}
