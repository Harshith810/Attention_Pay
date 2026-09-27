import { useApp } from '../app/AppProvider';
import { retrieveTransaction } from '../api/simulationApi';
export function useTransactionSimulation() {
  const { state, dispatch } = useApp();
  return async (scenario) => { dispatch({type:'SCENARIO_SELECT',scenario}); try { const data=await retrieveTransaction(scenario,state.stage2AccessToken); dispatch({type:'TRANSACTION_READY',transaction:data}); return data; } catch(e) { dispatch({type:'TRANSACTION_ERROR',error:e?.response?.data?.detail?.message || e.message || 'Unable to retrieve transaction.'}); throw e; } };
}
