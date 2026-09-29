import { useEffect, useState } from 'react';
import { useApp } from '../../app/AppProvider';
import { useStage1Analysis } from '../../hooks/useStage1Analysis';
import ErrorState from '../common/ErrorState';
export default function URLInputForm(){const {state}=useApp();const [url,setUrl]=useState(state.url || '');
  useEffect(()=>{ setUrl(state.url || ''); },[state.url]);const analyze=useStage1Analysis();const submit=async e=>{e.preventDefault();if(!url.trim())return;await analyze(url.trim()).catch(()=>{});};return <form className="url-form" onSubmit={submit}><label htmlFor="payment-url">Payment URL</label><div className="url-row"><input id="payment-url" value={url} onChange={e=>setUrl(e.target.value)} placeholder="https://example.com/payment" autoComplete="off"/><button className="primary-btn" disabled={state.stage1.status==='processing'}>{state.stage1.status==='processing'?'Analyzing…':'Analyze URL'}</button></div><p className="field-help">The URL is sent to the backend BERT classifier. The frontend does not make the phishing decision.</p><ErrorState message={state.error && state.stage1.status==='error'?state.error:null}/></form>}
