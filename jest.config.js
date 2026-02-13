module.exports = {
  testEnvironment: 'node',
  testPathIgnorePatterns: ['/node_modules/'],
  roots: ['<rootDir>/test/unit/aws-lambda', '<rootDir>/apps/aws-lambda'],
  testMatch: ['**/?(*.)+(spec|test).js'],
  collectCoverageFrom: [
    'apps/aws-lambda/**/*.js',
    '!apps/aws-lambda/node_modules/**',
    '!apps/aws-lambda/**/*.test.js',
  ],
};
