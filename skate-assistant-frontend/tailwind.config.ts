import type { Config } from "tailwindcss";

// Semantic design tokens (Story 1.3 - Design System Foundation)
const config: Config = {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
  	extend: {
		colors: {
			surface: 'hsl(var(--surface))',
			'surface-elevated': 'hsl(var(--surface-elevated))',
			'surface-overlay': 'hsl(var(--surface-overlay))',
			'text-primary': 'hsl(var(--text-primary))',
			'text-secondary': 'hsl(var(--text-secondary))',
			'text-muted': 'hsl(var(--text-muted))',
			border: 'hsl(var(--border))',
			'border-subtle': 'hsl(var(--border-subtle))',
			accent: {
				DEFAULT: 'hsl(var(--accent))',
				foreground: 'hsl(var(--text-primary))'
			},
			grounded: 'hsl(var(--grounded))',
			uncertain: 'hsl(var(--uncertain))',
			error: 'hsl(var(--error))',
			background: 'hsl(var(--surface))',
			foreground: 'hsl(var(--text-primary))',
			primary: {
				DEFAULT: 'hsl(var(--accent))',
				foreground: 'hsl(var(--text-primary))'
			},
			secondary: {
				DEFAULT: 'hsl(var(--surface-elevated))',
				foreground: 'hsl(var(--text-secondary))'
			},
			muted: {
				DEFAULT: 'hsl(var(--surface-elevated))',
				foreground: 'hsl(var(--text-muted))'
			},
			input: 'hsl(var(--border))',
			ring: 'hsl(var(--accent))'
		},
  		borderRadius: {
  			none: '0',
  			sm: '4px',
  			full: '9999px'
  		},
  		fontSize: {
  			'display-1': [
  				'48px',
  				{
  					lineHeight: '1.1'
  				}
  			],
  			'display-2': [
  				'40px',
  				{
  					lineHeight: '1.15'
  				}
  			],
  			'headline-1': [
  				'32px',
  				{
  					lineHeight: '1.2'
  				}
  			],
  			'headline-2': [
  				'24px',
  				{
  					lineHeight: '1.25'
  				}
  			],
  			'body-large': [
  				'18px',
  				{
  					lineHeight: '1.5'
  				}
  			],
  			body: [
  				'16px',
  				{
  					lineHeight: '1.5'
  				}
  			],
  			caption: [
  				'14px',
  				{
  					lineHeight: '1.4'
  				}
  			],
  			tag: [
  				'12px',
  				{
  					lineHeight: '1.2',
  					letterSpacing: '0.1em'
  				}
  			],
  			'mono-body': [
  				'16px',
  				{
  					lineHeight: '1.5'
  				}
  			],
  			'mono-caption': [
  				'14px',
  				{
  					lineHeight: '1.4'
  				}
  			]
  		},
		fontFamily: {
			sans: [
				'var(--font-geist-sans)',
				'system-ui',
				'-apple-system',
				'BlinkMacSystemFont',
				'Segoe UI',
				'Roboto',
				'sans-serif'
			],
			mono: [
				'var(--font-geist-mono)',
				'ui-monospace',
				'SF Mono',
				'Menlo',
				'Monaco',
				'Cascadia Code',
				'Courier New',
				'monospace'
			]
		},
  		keyframes: {
  			'accordion-down': {
  				from: {
  					height: '0'
  				},
  				to: {
  					height: 'var(--radix-accordion-content-height)'
  				}
  			},
  			'accordion-up': {
  				from: {
  					height: 'var(--radix-accordion-content-height)'
  				},
  				to: {
  					height: '0'
  				}
  			}
  		},
  		animation: {
  			'accordion-down': 'accordion-down 0.2s ease-out',
  			'accordion-up': 'accordion-up 0.2s ease-out'
  		}
  	}
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
