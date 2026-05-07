import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { Popover, PopoverContent, PopoverTrigger } from './popover';
import { Button } from './button';

const meta = {
  title: 'UI/Popover',
  component: Popover,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Popover>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline">Open popover</Button>
      </PopoverTrigger>
      <PopoverContent className="w-80">
        <div className="space-y-2">
          <h4 className="font-medium leading-none">Popover</h4>
          <p className="text-sm text-text-secondary">
            This is a popover with some content.
          </p>
        </div>
      </PopoverContent>
    </Popover>
  ),
};
