module.exports = {
  testEnvironment: 'node',
  testPathIgnorePatterns: ['/node_modules/', '/.venv/'],
  rootDir: '../../',
  testMatch: ['<rootDir>/test/unit/aws-lambda/**/*.test.js'],
  moduleDirectories: ['node_modules', '<rootDir>/apps/aws-lambda/node_modules'],
  collectCoverageFrom: [
    'apps/aws-lambda/**/*.js',
    '!apps/aws-lambda/node_modules/**',
    '!apps/aws-lambda/**/*.test.js',
  ],
};
