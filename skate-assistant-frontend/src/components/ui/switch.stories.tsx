import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { Switch } from './switch';

const meta = {
  title: 'UI/Switch',
  component: Switch,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Switch>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <div className="flex items-center space-x-2">
      <Switch id="airplane-mode" />
      <label htmlFor="airplane-mode" className="text-sm font-medium cursor-pointer">
        Airplane Mode
      </label>
    </div>
  ),
};

export const Disabled: Story = {
  render: () => (
    <div className="flex items-center space-x-2">
      <Switch id="disabled" disabled />
      <label htmlFor="disabled" className="text-sm font-medium text-text-muted">
        Disabled
      </label>
    </div>
  ),
};
