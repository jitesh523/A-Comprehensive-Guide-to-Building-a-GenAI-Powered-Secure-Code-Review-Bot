import securityPlugin from "eslint-plugin-security";
import noUnsanitized from "eslint-plugin-no-unsanitized";
import globals from "globals";

export default [
  {
    plugins: {
      security: securityPlugin,
      "no-unsanitized": noUnsanitized,
    },
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: {
        ...globals.node,
        ...globals.browser,
      },
    },
    rules: {
      ...securityPlugin.configs.recommended.rules,
      ...noUnsanitized.configs.recommended.rules,
      // Disable non-security rules to reduce noise
      "no-unused-vars": "off",
      "no-console": "off",
    },
  }
];
