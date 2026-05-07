import type { Preview } from '@storybook/nextjs-vite'
import '../src/app/globals.css'

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
       color: /(background|color)$/i,
       date: /Date$/i,
      },
    },
    backgrounds: {
      default: 'dark',
      values: [
        { name: 'dark', value: '#000000' },
        { name: 'light', value: '#FFFFFF' },
      ],
    },
  },
  decorators: [
    (Story) => (
      <div className="dark">
        <div className="bg-surface text-text-primary p-4 min-h-screen">
          <Story />
        </div>
      </div>
    ),
  ],
};

export default preview;