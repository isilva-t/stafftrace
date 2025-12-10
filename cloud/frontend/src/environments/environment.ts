export const environment = {
  production: false,
  apiUrl: 'http://localhost:8080/api', // this variable is changed in build time,
  // on production to '/api'. check Dockerfile and see sed
  refreshInterval: 15000,
  locale: 'en-GB'
};
