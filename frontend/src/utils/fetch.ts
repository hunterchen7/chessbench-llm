const BASE_URL = 'https://worker.hunter-chen7.workers.dev';

export const fetchWithPrefix = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
  const response = await fetch(BASE_URL + input, init);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response;
};