export const environment = {
  production: false,
  apiUrl: 'http://stafftrace.xyz:8080/api', // this variable is changed in build time,docker-co
  // on production to '/api'. check Dockerfile and see sed
  refreshInterval: 15000,
  locale: 'en-GB',
  healthy: 350,
  degraded: 700,
};
