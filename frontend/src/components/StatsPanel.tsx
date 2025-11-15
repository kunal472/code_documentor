'use client';

import React from 'react';
import { useStore } from '@/lib/store';
import { FileNode } from '@/lib/types';

function StatsPanel() {
    const {
        dependencies,
        hierarchy,
        // --- NEW: Get graph node counts ---
        originalGraphNodes,
        graphNodes
        // --- END NEW ---
    } = useStore((state) => ({
        dependencies: state.dependencies,
        hierarchy: state.hierarchy,
        originalGraphNodes: state.originalGraphNodes,
        graphNodes: state.graphNodes,
    }));

    if (!dependencies || !hierarchy) {
        return (
            <div className="text-muted-foreground">
                No statistics available. Please run an analysis.
            </div>
        );
    }

    // This logic is fine, it counts from the hierarchy
    const fileCount = React.useMemo(() => {
        let count = 0;
        function traverse(node: any) {
            if (node.children) {
                node.children.forEach(traverse);
            } else {
                count++;
            }
        }
        traverse(hierarchy);
        return count;
    }, [hierarchy]);

    return (
        <div className="space-y-8">
            <div className="p-4 bg-background rounded-lg">
                <h2 className="text-xl font-semibold mb-4">Repository Stats</h2>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div>
                        <p className="text-sm text-muted-foreground">Total Files Scanned</p>
                        <p className="text-2xl font-bold">{fileCount}</p>
                    </div>
                    <div>
                        <p className="text-sm text-muted-foreground">Isolated Files</p>
                        <p className="text-2xl font-bold">{dependencies.isolated_files.length}</p>
                    </div>
                    <div>
                        <p className="text-sm text-muted-foreground">Circular Dependencies</p>
                        <p className="text-2xl font-bold">{dependencies.circular_dependencies.length}</p>
                    </div>
                    {/* --- NEW: Live Node Counter --- */}
                    <div className="col-span-2 md:col-span-3">
                        <p className="text-sm text-muted-foreground">Graph Nodes Displayed</p>
                        <p className="text-2xl font-bold">
                            {graphNodes.length}
                            <span className="text-lg text-muted-foreground">
                {" "} / {originalGraphNodes.length}
              </span>
                        </p>
                        <p className="text-xs text-muted-foreground">
                            (Filtered nodes / Total nodes)
                        </p>
                    </div>
                    {/* --- END NEW --- */}
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* ... (Most Imported Files) ... */}
                <div className="p-4 bg-background rounded-lg">
                    <h2 className="text-xl font-semibold mb-4">Most Imported Files</h2>
                    <ul className="space-y-2">
                        {dependencies.most_imported.map((file) => (
                            <li key={file.path} className="flex justify-between text-sm">
                                <span className="truncate text-primary" title={file.path}>{file.path}</span>
                                <span className="font-mono bg-secondary px-2 py-0.5 rounded-md">{file.imported_by_count}</span>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* ... (Most Importing Files) ... */}
                <div className="p-4 bg-background rounded-lg">
                    <h2 className="text-xl font-semibold mb-4">Most Importing Files</h2>
                    <ul className="space-y-2">
                        {dependencies.most_importing.map((file) => (
                            <li key={file.path} className="flex justify-between text-sm">
                                <span className="truncate text-primary" title={file.path}>{file.path}</span>
                                <span className="font-mono bg-secondary px-2 py-0.5 rounded-md">{file.imports_count}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            </div>

            {/* ... (Circular Dependencies) ... */}
            {dependencies.circular_dependencies.length > 0 && (
                <div className="p-4 bg-background rounded-lg border border-red-500/50">
                    <h2 className="text-xl font-semibold mb-4 text-red-400">Circular Dependencies Found</h2>
                    <ul className="space-y-4">
                        {dependencies.circular_dependencies.map((cycle, index) => (
                            <li key={index} className="text-sm">
                                <p className="font-semibold mb-2">Cycle {index + 1}</p>
                                <ul className="list-disc pl-5 space-y-1 text-muted-foreground">
                                    {cycle.nodes.map(node => (
                                        <li key={node} className="font-mono">{node}</li>
                                    ))}
                                </ul>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}

export default StatsPanel;