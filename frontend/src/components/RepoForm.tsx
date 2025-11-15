'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useStore } from '@/lib/store';
import LoadingSpinner from './LoadingSpinner';

export function RepoForm() {
    const router = useRouter();
    const [url, setUrl] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const setRepoUrl = useStore((state) => state.setRepoUrl);

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        if (!url) return;

        setIsLoading(true);
        setRepoUrl(url); // Set in store

        // Navigate to the analysis page
        // The analysis page will trigger the API call
        router.push(`/analyze?repo=${encodeURIComponent(url)}`);
    };

    return (
        <form
            onSubmit={handleSubmit}
            className="flex w-full items-center space-x-2"
        >
            <Input
                type="text"
                placeholder="https"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={isLoading}
                className="flex-1"
            />
            <Button type="submit" disabled={isLoading || !url} size="lg">
                {isLoading ? <LoadingSpinner size={20} /> : 'Analyze'}
            </Button>
        </form>
    );
}