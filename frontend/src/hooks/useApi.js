// Small helper: run an API call when the page loads and track loading / error / data.
// Usage: const { data, error, loading } = useApi(() => getCall(id), [id]);
import { useEffect, useState } from 'react';

export default function useApi(fetcher, deps) {
  const [state, setState] = useState({ data: null, error: null, loading: true });

  useEffect(() => {
    let cancelled = false;
    setState({ data: null, error: null, loading: true });

    fetcher()
      .then((data) => !cancelled && setState({ data, error: null, loading: false }))
      .catch((error) => !cancelled && setState({ data: null, error, loading: false }));

    return () => {
      cancelled = true; // ignore the result if the user already left the page
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return state;
}
