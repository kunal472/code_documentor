'use client';

import React from 'react';
import { useReactFlow, Panel } from 'reactflow';
import { ZoomIn, ZoomOut, Minimize2, Download, Search } from 'lucide-react';
import { toPng } from 'html-to-image';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Checkbox } from './ui/checkbox';
import { useStore, NodeFilters } from '@/lib/store';
import { Language } from '@/lib/types';
import { cn } from '@/lib/utils';

// --- NEW: Language colors helper ---
const getLanguageColor = (lang: string) => {
    switch (lang) {
        case 'python': return 'bg-blue-500';
        case 'javascript': return 'bg-yellow-500';
        case 'typescript': return 'bg-sky-500';
        default: return 'bg-gray-500';
    }
};
// --- END NEW ---

function GraphControls() {
    const { zoomIn, zoomOut, fitView } = useReactFlow();

    // --- NEW: Get search/filter state from store ---
    const {
        searchQuery,
        nodeFilters,
        setSearchQuery,
        setNodeFilters
    } = useStore((state) => ({
        searchQuery: state.searchQuery,
        nodeFilters: state.nodeFilters,
        setSearchQuery: state.setSearchQuery,
        setNodeFilters: state.setNodeFilters,
    }));
    // --- END NEW ---

    const onExport = () => {
        // ... (This function remains unchanged) ...
        const reactFlowViewport = document.querySelector('.react-flow__viewport') as HTMLElement;
        if (reactFlowViewport) {
            toPng(reactFlowViewport, {
                backgroundColor: 'hsl(var(--secondary))',
                cacheBust: true,
            })
                .then((dataUrl) => {
                    const a = document.createElement('a');
                    a.href = dataUrl;
                    a.download = 'code-graph.png';
                    a.click();
                })
                .catch((err) => console.error('Failed to export graph', err));
        }
    };

    // --- NEW: Filter change handler ---
    const handleFilterChange = (lang: Language) => {
        const newFilters: NodeFilters = {
            ...nodeFilters,
            [lang]: !nodeFilters[lang],
        };
        setNodeFilters(newFilters);
    };
    // --- END NEW ---

    return (
        <Panel position="top-right" className="flex flex-col gap-2 p-4 bg-background/80 border border-border rounded-lg shadow-lg backdrop-blur-sm">
            {/* Search Bar */}
            <div className="relative w-full">
                <Input
                    type="text"
                    placeholder="Search nodes..."
                    className="pl-8"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
                <Search size={16} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
            </div>

            {/* View Controls */}
            <div className="flex space-x-2">
                <Button variant="outline" size="icon" onClick={() => zoomIn()} title="Zoom In">
                    <ZoomIn size={18} />
                </Button>
                <Button variant="outline" size="icon" onClick={() => zoomOut()} title="Zoom Out">
                    <ZoomOut size={18} />
                </Button>
                <Button variant="outline" size="icon" onClick={() => fitView()} title="Fit View">
                    <Minimize2 size={18} />
                </Button>
                <Button variant="outline" size="icon" onClick={onExport} title="Export as PNG">
                    <Download size={18} />
                </Button>
            </div>

            {/* Filter Controls */}
            <div className="flex flex-col space-y-2 pt-2">
                <p className="text-sm font-medium">Filter Nodes</p>
                {(Object.keys(nodeFilters) as Language[]).map((lang) => (
                    <div key={lang} className="flex items-center space-x-2">
                        <Checkbox
                            id={lang}
                            checked={nodeFilters[lang]}
                            onCheckedChange={() => handleFilterChange(lang)}
                        />
                        <label
                            htmlFor={lang}
                            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 flex items-center"
                        >
                            <span className={cn('w-3 h-3 rounded-full mr-2', getLanguageColor(lang))}></span>
                            {lang.charAt(0).toUpperCase() + lang.slice(1)}
                        </label>
                    </div>
                ))}
            </div>
        </Panel>
    );
}

export default GraphControls;