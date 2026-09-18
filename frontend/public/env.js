// Local development default. In Docker/Render deployments this file is
// regenerated at container start (see docker-entrypoint.sh) from the
// API_BASE_URL / WS_BASE_URL environment variables, so the same built
// frontend image can point at different backend URLs without a rebuild.
window.__ENV__ = {
  API_BASE_URL: "http://localhost:8000",
  WS_BASE_URL: "ws://localhost:8000",
};
