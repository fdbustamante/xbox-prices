import js from '@eslint/js';
import globals from 'globals';
import tseslint from '@typescript-eslint/eslint-plugin';
import tsParser from '@typescript-eslint/parser';
import reactPlugin from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import vitestPlugin from 'eslint-plugin-vitest'; // Import vitest plugin

export default [
  { ignores: ['dist', 'node_modules'] },
  // Main configuration for source files
  {
    files: ['src/**/*.{js,jsx,ts,tsx}'], // More specific to src for app code
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      parser: tsParser,
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
      globals: {
        ...globals.browser,
        ...globals.es2021,
      },
    },
    plugins: {
      '@typescript-eslint': tseslint,
      'react': reactPlugin,
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
    rules: {
      ...js.configs.recommended.rules,
      ...tseslint.configs.recommended.rules,
      ...reactPlugin.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      'no-unused-vars': 'off', // Disable base rule, use TS version
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],
      'react/react-in-jsx-scope': 'off',
      'react/prop-types': 'off',
    },
  },
  // Configuration for test files
  {
    files: ['src/__tests__/**/*.{ts,tsx}', '**/*.test.{ts,tsx}'], // Target test files
    plugins: {
      vitest: vitestPlugin,
    },
    languageOptions: {
      globals: {
        ...vitestPlugin.environments.env.globals, // Add vitest globals
      },
    },
    rules: {
      ...vitestPlugin.configs.recommended.rules,
    },
  },
  // Configuration for JS config files (like this one, vite.config.js, vitest.config.ts)
  {
    files: ['*.js', '*.cjs', '*.mjs', '*.config.js', '*.config.ts', 'vitest.config.ts'], // Added vitest.config.ts
    languageOptions: {
      globals: {
        ...globals.node,
      },
    },
    rules: { // Relax some rules for config files
        '@typescript-eslint/no-var-requires': 'off',
        'no-undef': 'off' // Allow 'module' in commonjs config files if any
    }
  }
];
