import { createContext, useContext, useMemo, useReducer } from 'react';
import { sessionReducer, initialSession } from '../state/sessionReducer';

const AppContext = createContext(null);
export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(sessionReducer, initialSession);
  const value = useMemo(() => ({ state, dispatch }), [state]);
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}
export function useApp() {
  const value = useContext(AppContext);
  if (!value) throw new Error('useApp must be used inside AppProvider');
  return value;
}
