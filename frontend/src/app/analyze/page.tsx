'use client';

import React from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useStore } from '@/lib/store';
import { useEffect } from 'react';
import CodeGraph from '@/components/CodeGraph';
import DocumentationViewer from '@/components/DocumentationViewer';
import StatsPanel from '@/components/StatsPanel';
import LoadingSpinner from '@/components/LoadingSpinner';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertCircle, ArrowLeft } from 'lucide-react';

export default function AnalyzePage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const repoUrl = searchParams.get('repo');

    const { status, error, startAnalysis } = useStore((state) => ({
        status: state.status,
        error: state.error,
        startAnalysis: state.startAnalysis,
    }));

    useEffect(() => {
        if (!repoUrl) {
            router.push('/');
            return;
        }

        // Only start analysis if we are idle (e.g., page load)
        if (status === 'idle') {
            startAnalysis(repoUrl);
        }
    }, [repoUrl, router, startAnalysis, status]);

    const renderContent = () => {
        if (status === 'loading_graph') {
            return (
                <div className="flex flex-col items-center justify-center h-[70vh]">
                    <LoadingSpinner size={64} />
                    <p className="mt-4 text-lg text-muted-foreground">
                        Analyzing repository...
                    </p>
                    <p className="text-sm text-muted-foreground/70">
                        This may take a moment.
                    </p>
                </div>
            );
        }

        if (status === 'error') {
            return (
                <div className="flex flex-col items-center justify-center h-[70vh] text-red-500">
                    <AlertCircle size={48} />
                    <p className="mt-4 text-lg">Analysis Failed</p>
                    <p className="mt-2 text-sm bg-secondary p-4 rounded-md">
                        {error}
                    </p>
                </div>
            );
        }

        if (status === 'success' || status === 'streaming_docs') {
            return (
                <Tabs defaultValue="graph" className="w-full">
                    <TabsList className="grid w-full grid-cols-3 mb-4">
                        <TabsTrigger value="graph">Graph</TabsTrigger>
                        <TabsTrigger value="documentation">Documentation</TabsTrigger>
                        <TabsTrigger value="statistics">Statistics</TabsTrigger>
                    </TabsList>

                    <TabsContent value="graph">
                        <div className="w-full h-[75vh] rounded-lg border bg-secondary">
                            <CodeGraph />
                        </div>
                    </TabsContent>

                    <TabsContent value="documentation">
                        <div className="w-full h-[75vh] rounded-lg border bg-secondary p-4 overflow-auto">
                            <DocumentationViewer />
                        </div>
                    </TabsContent>

                    <TabsContent value="statistics">
                        <div className="w-full h-[75vh] rounded-lg border bg-secondary p-4 overflow-auto">
                            <StatsPanel />
                        </div>
                    </TabsContent>
                </Tabs>
            );
        }
    };

    return (
        <main className="flex min-h-screen flex-col p-8">
            <div className="flex items-center justify-between mb-6">
                <button
                    onClick={() => router.push('/')}
                    className="flex items-center text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                    <ArrowLeft size={16} className="mr-2" />
                    Back to Home
                </button>
                <h1 className="text-xl font-semibold truncate max-w-2xl">
                    {repoUrl || 'Analysis'}
                </h1>
                <div className="w-24"></div> {/* Spacer */}
            </div>

            {renderContent()}
        </main>
    );
}