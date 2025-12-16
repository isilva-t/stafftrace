export const environment = {
  production: false,
  apiUrl: '/api', // this variable is changed in build time,docker-co
  // on production to '/api'. check Dockerfile and see sed
  refreshInterval: 15000,
  locale: 'en-GB',
  healthy: 350,
  degraded: 700,
};
