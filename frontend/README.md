# AttentionPay Frontend

React/Vite frontend for the AttentionPay payment-security console. The implementation follows the finalized Frontend Implementation Guide and consumes the existing FastAPI contracts on `feat-backend`.

## Run

```bash
npm install
cp .env.example .env
npm run dev
```

Set `VITE_API_BASE_URL` to the FastAPI base URL.

## Current build

- Stage 1 URL analysis
- Stage 2 access token held only in React memory
- Five scenario cards
- PostgreSQL transaction preview
- Synchronous processing pipeline
- Impossible Travel map for Stage 2
- Layer 1 rule explanation
- TabTransformer probability/result
- SHAP/LIME visualizations
- Random transaction run-again flow
- Backend-driven final state
