import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { Toast } from './toast';
import { useToast } from '@/hooks/use-toast';
import { Button } from './button';
import { Toaster } from './toaster';

const meta = {
  title: 'UI/Toast',
  component: Toast,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Toast>;

export default meta;
type Story = StoryObj<typeof meta>;

function ToastDemo() {
  const { toast } = useToast();

  return (
    <>
      <Button
        variant="outline"
        onClick={() => {
          toast({
            title: "Notification",
            description: "This is a toast notification.",
          });
        }}
      >
        Show Toast
      </Button>
      <Toaster />
    </>
  );
}

export const Default: Story = {
  render: () => <ToastDemo />,
};
