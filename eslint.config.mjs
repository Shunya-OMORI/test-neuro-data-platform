// /eslint.config.mjs
import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import eslintConfigPrettier from 'eslint-config-prettier';
import globals from 'globals';

export default tseslint.config(
  // 1. Global ignores for all configurations
  {
    ignores: [
      '**/node_modules/**',
      '**/dist/**',
      '**/.venv/**',
      '**/bids_output/**',
    ],
  },
  
  // 2. Base recommended configurations
  js.configs.recommended,
  ...tseslint.configs.recommendedTypeChecked,
  ...tseslint.configs.stylisticTypeChecked,
  
  // 3. Configuration for all TypeScript files in the workspace
  {
    files: ['apps/*/src/**/*.ts', 'packages/*/src/**/*.ts'],
    languageOptions: {
      // Set parser options for type-aware linting in a monorepo
      parserOptions: {
        project: true, // Automatically find tsconfig.json for each file
        tsconfigRootDir: import.meta.dirname,
      },
      // Define global variables for the Node.js environment
      globals: {
        ...globals.node,
      },
    },
    rules: {
      // Customize rules here. For example, allow console logs during development.
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      '@typescript-eslint/no-unused-vars': [
        'warn',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
    },
  },
  
  // 4. Prettier config must be last to override styling rules
  eslintConfigPrettier,
);