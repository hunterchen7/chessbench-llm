const BASE_URL = 'https://chessbench.hunterchen.workers.dev/api/chessbench';

export const fetchWithPrefix = async (
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<Response> => {
  const response = await fetch(BASE_URL + input, init);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response;
};
