import { useApp } from '../app/AppProvider';
import { analyzeUrl } from '../api/phishingApi';
export function useStage1Analysis() {
  const { dispatch } = useApp();
  return async (url) => { dispatch({type:'URL_SUBMIT',url}); try { const response=await analyzeUrl(url); dispatch({type:'URL_RESULT',response}); return response; } catch (e) { dispatch({type:'URL_ERROR',error:e?.response?.data?.detail?.message || e.message || 'Unable to analyze URL.'}); throw e; } };
}
