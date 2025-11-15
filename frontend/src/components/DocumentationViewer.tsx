'use client';

import React, { useState, useMemo } from 'react';
import { useStore } from '@/lib/store';
import { Button } from './ui/button';
import LoadingSpinner from './LoadingSpinner';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check, Search } from 'lucide-react';
import { Input } from './ui/input'; // Import Input

// ... (MarkdownRenderer component remains unchanged from Phase 4) ...
const MarkdownRenderer = ({ content }: { content: string }) => {
    const [copied, setCopied] = useState(false);
    const handleCopy = (code: string) => {
        navigator.clipboard.writeText(code);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };
    return (
        <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw]}
            components={{
                h1: ({ ...props }) => <h1 className="text-3xl font-bold mt-6 mb-4" {...props} />,
                h2: ({ ...props }) => <h2 className="text-2xl font-semibold mt-5 mb-3 border-b pb-2" {...props} />,
                h3: ({ ...props }) => <h3 className="text-xl font-semibold mt-4 mb-2" {...props} />,
                p: ({ ...props }) => <p className="mb-4" {...props} />,
                ul: ({ ...props }) => <ul className="list-disc pl-6 mb-4" {...props} />,
                li: ({ ...props }) => <li className="mb-2" {...props} />,
                code: ({ node, inline, className, children, ...props }) => {
                    const match = /language-(\w+)/.exec(className || '');
                    const codeString = String(children).replace(/\n$/, '');
                    return !inline ? (
                        <div className="relative my-4">
                            <button
                                className="absolute top-2 right-2 p-1.5 rounded-md bg-secondary text-muted-foreground hover:bg-background transition-colors"
                                onClick={() => handleCopy(codeString)}
                            >
                                {copied ? <Check size={16} /> : <Copy size={16} />}
                            </button>
                            <SyntaxHighlighter
                                {...props}
                                style={vscDarkPlus}
                                language={match ? match[1] : 'text'}
                                PreTag="div"
                            >
                                {codeString}
                            </SyntaxHighlighter>
                        </div>
                    ) : (
                        <code className="px-1.5 py-0.5 bg-secondary rounded-md text-primary" {...props}>
                            {children}
                        </code>
                    );
                },
            }}
        >
            {content}
        </ReactMarkdown>
    );
};


function DocumentationViewer() {
    const { status, docFiles, streamLogs, streamProgress, startStreaming } = useStore();

    // --- NEW: Local state for doc search ---
    const [docSearch, setDocSearch] = useState('');
    // --- END NEW ---

    const allDocs = useMemo(() => Object.values(docFiles), [docFiles]);

    // --- NEW: Filtered docs logic ---
    const filteredDocs = useMemo(() => {
        if (!docSearch) return allDocs;
        const lowerQuery = docSearch.toLowerCase();
        return allDocs.filter(
            (doc) =>
                doc.path.toLowerCase().includes(lowerQuery) ||
                doc.summary.toLowerCase().includes(lowerQuery) ||
                doc.documentation.toLowerCase().includes(lowerQuery)
        );
    }, [allDocs, docSearch]);
    // --- END NEW ---


    const renderStreamProgress = () => {
        // ... (This function remains unchanged) ...
        if (status !== 'streaming_docs') return null;
        const percent = streamProgress.total > 0 ? (streamProgress.processed / streamProgress.total) * 100 : 0;
        return (
            <div className="w-full mb-4">
                <p className="text-sm text-muted-foreground mb-2">
                    Generating... ({streamProgress.processed} / {streamProgress.total})
                </p>
                <div className="w-full bg-background rounded-full h-2.5">
                    <div className="bg-primary h-2.5 rounded-full transition-all" style={{ width: `${percent}%` }}></div>
                </div>
                <div className="h-32 overflow-auto bg-background p-2 rounded-md mt-2 text-xs text-muted-foreground">
                    {streamLogs.map((log, i) => <p key={i}>&gt; {log}</p>)}
                </div>
            </div>
        );
    };

    if (allDocs.length === 0 && status !== 'streaming_docs') {
        return (
            <div className="flex flex-col items-center justify-center h-full text-center">
                <p className="text-lg text-muted-foreground">
                    No documentation generated yet.
                </p>
                <Button onClick={startStreaming} className="mt-4">
                    Generate All Documentation
                </Button>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full">
            {renderStreamProgress()}

            {status === 'streaming_docs' && allDocs.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full">
                    <LoadingSpinner size={48} />
                    <p className="text-lg text-muted-foreground mt-4">Waiting for first file...</p>
                </div>
            )}

            {/* --- NEW: Search bar for docs --- */}
            {allDocs.length > 0 && (
                <div className="relative mb-4">
                    <Input
                        type="text"
                        placeholder="Search documentation..."
                        className="pl-8"
                        value={docSearch}
                        onChange={(e) => setDocSearch(e.target.value)}
                    />
                    <Search size={16} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
                </div>
            )}
            {/* --- END NEW --- */}

            <div className="space-y-6">
                {/* --- MODIFIED: Use filteredDocs --- */}
                {filteredDocs
                    .sort((a, b) => a.path.localeCompare(b.path))
                    .map((doc) => (
                        <div key={doc.path} className="pb-6 border-b border-border last:border-b-0">
                            <h2 className="text-2xl font-semibold text-primary mb-2">
                                {doc.path}
                            </h2>
                            <p className="text-md italic text-muted-foreground mb-4">
                                {doc.summary}
                            </p>
                            <MarkdownRenderer content={doc.documentation} />
                        </div>
                    ))}

                {filteredDocs.length === 0 && docSearch.length > 0 && (
                    <p className="text-muted-foreground text-center">
                        No documentation found matching "{docSearch}".
                    </p>
                )}
            </div>
        </div>
    );
}

export default DocumentationViewer;