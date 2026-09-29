import { useApp } from '../../app/AppProvider';
export default function URLProcessingAnimation(){const {state}=useApp();if(state.stage1.status!=='processing')return null;return <div className="processing-sequence" aria-live="polite">{['URL submitted','URL received','Tokenizing URL','Security decision'].map((s,i)=><div className="sequence-step" key={s}><span>{i+1}</span>{s}</div>)}</div>}
