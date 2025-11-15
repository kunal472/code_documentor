import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LoadingSpinnerProps {
    size?: number;
    className?: string;
}

const LoadingSpinner = ({ size = 24, className }: LoadingSpinnerProps) => {
    return (
        <Loader2
            size={size}
            className={cn('animate-spin text-primary', className)}
        />
    );
};

export default LoadingSpinner;