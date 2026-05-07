// For more info, see https://github.com/storybookjs/eslint-plugin-storybook#configuration-flat-config-format
//
// ACCESSIBILITY REQUIREMENT (Story 1.3 - Design System Foundation):
// ==================================================================
// All interactive elements (buttons, links, Radix Primitives with click handlers)
// MUST meet a 44 × 44 pixel touch target (NFR30 from PRD).
//
// ENFORCEMENT STATUS: Manual PR review required until automated lint rule lands in Story 1.18.
// - Check all <button>, <a>, and Radix interactive components (e.g., DialogTrigger, TabsTrigger)
// - Ensure adequate padding, min-width, min-height to reach 44x44px
// - This is a WCAG 2.2 AA requirement and blocks merge if violated during PR review
//
import storybook from "eslint-plugin-storybook";

import { FlatCompat } from "@eslint/eslintrc";

const compat = new FlatCompat({ baseDirectory: import.meta.dirname });

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  ...storybook.configs["flat/recommended"]
];

export default eslintConfig;
