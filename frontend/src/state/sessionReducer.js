export const initialSession = {
  url: '',
  stage1: { status: 'idle', response: null },
  stage2AccessToken: null,
  selectedScenario: null,
  transaction: null,
  transactionStatus: 'idle',
  processingResponse: null,
  pipeline: { transactionRetrieved:'pending', featureEngineering:'pending', apiRouteIntegrity:'pending', impossibleTravel:'pending', tabTransformer:'pending', explainability:'pending', finalDecision:'pending' },
  error: null,
  currentPage: 'setup',
};

export function sessionReducer(state, action) {
  switch (action.type) {
    case 'URL_SUBMIT':
      // A new Stage 1 check starts a fresh security path. Do not leave old
      // Stage 2/results access available while the new URL is being checked.
      return {
        ...state,
        url: action.url,
        stage1:{status:'processing',response:null},
        stage2AccessToken:null,
        selectedScenario:null,
        transaction:null,
        transactionStatus:'idle',
        processingResponse:null,
        pipeline:initialSession.pipeline,
        currentPage:'setup',
        error:null,
      };

    case 'URL_RESULT': {
      const blocked = Boolean(action.response.blocked);
      return {
        ...state,
        stage1:{status:blocked?'blocked':'completed',response:action.response},
        // A blocked/phishing Stage 1 result is a hard gate: no Stage 2 token,
        // transaction, processing result, or navigation access survives it.
        stage2AccessToken:blocked ? null : (action.response.stage2_access_token ?? null),
        selectedScenario:blocked ? null : state.selectedScenario,
        transaction:blocked ? null : state.transaction,
        transactionStatus:blocked ? 'idle' : state.transactionStatus,
        processingResponse:blocked ? null : state.processingResponse,
        pipeline:blocked ? initialSession.pipeline : state.pipeline,
        currentPage:'setup',
        error:null,
      };
    }

    case 'URL_ERROR':
      return {...state, stage1:{...state.stage1,status:'error'}, error:action.error, currentPage:'setup'};
    case 'SCENARIO_SELECT': return {...state, selectedScenario:action.scenario, transaction:null, transactionStatus:'retrieving', processingResponse:null, pipeline:initialSession.pipeline, error:null};
    case 'TRANSACTION_READY': return {...state, transaction:action.transaction, transactionStatus:'ready', error:null, currentPage:'transaction', pipeline:{...state.pipeline,transactionRetrieved:'passed'}};
    case 'TRANSACTION_ERROR': return {...state, transactionStatus:'error', error:action.error};
    case 'PROCESS_START': return {...state, transactionStatus:'processing', error:null, pipeline:{...state.pipeline,transactionRetrieved:'passed'}};
    case 'PROCESS_RESULT': return {...state, transactionStatus:'completed', processingResponse:action.response, pipeline:action.pipeline, currentPage:'transaction', error:null};
    case 'PROCESS_ERROR': return {...state, transactionStatus:'error', error:action.error};
    case 'NAVIGATE_PAGE': return {...state, currentPage: action.page};
    case 'RESET_SESSION': return initialSession;
    default: return state;
  }
}
