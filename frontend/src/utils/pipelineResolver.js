export function resolvePipeline(response) {
  const blockedByLayer1 = response.layer === 'layer_1_security' && response.decision === 'BLOCK';
  const apiPassed = response.checks?.api_route_integrity?.passed;
  const travelPassed = response.checks?.impossible_travel?.passed;

  return {
    transactionRetrieved: 'passed',
    apiRouteIntegrity: apiPassed === true
      ? 'passed'
      : apiPassed === false
        ? 'blocked'
        : blockedByLayer1
          ? 'blocked'
          : 'skipped',
    impossibleTravel: travelPassed === true
      ? 'passed'
      : travelPassed === false
        ? 'blocked'
        : blockedByLayer1
          ? 'blocked'
          : 'skipped',
    featureEngineering: blockedByLayer1 ? 'skipped' : 'passed',
    tabTransformer: response.ai_executed
      ? (response.prediction === 'Fraud' ? 'blocked' : 'passed')
      : 'skipped',
    explainability: response.ai_executed ? 'completed' : 'skipped',
    finalDecision: response.decision === 'BLOCK' ? 'blocked' : 'approved',
  };
}
