'use client';

import React, { useCallback, useMemo } from 'react';
import ReactFlow, {
    Background,
    Controls,
    MiniMap,
    Node,
    Edge,
    Position,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useStore } from '@/lib/store';
import GraphControls from './GraphControls';
import { cn } from '@/lib/utils'; // Import cn

// Custom Node component
// --- MODIFIED: Accept isHighlighted prop ---
const CustomNode = ({ data }: { data: { label: string; language: string; isHighlighted: boolean } }) => {
    const getLanguageColor = (lang: string) => {
        switch (lang) {
            case 'python': return 'bg-blue-500';
            case 'javascript': return 'bg-yellow-500';
            case 'typescript': return 'bg-sky-500';
            default: return 'bg-gray-500';
        }
    };

    return (
        // The highlight style is now applied directly by the store
        // to the node's `style` prop, so no need for cn() here.
        <div className="react-flow__node-custom">
            <div className="flex items-center justify-between">
                <span className="truncate" title={data.label}>{data.label}</span>
                <span
                    className={cn(
                        'w-3 h-3 rounded-full ml-2',
                        getLanguageColor(data.language)
                    )}
                    title={data.language}
                ></span>
            </div>
            {/* Handles are implicitly added by React Flow */}
        </div>
    );
};
// --- END MODIFICATION ---

// Custom Error Node component
// --- MODIFIED: Accept isHighlighted prop ---
const CustomErrorNode = ({ data }: { data: { label: string; language: string; isHighlighted: boolean } }) => {
    return (
        <div className="react-flow__node-customError" title="Part of a circular dependency">
            <div className="flex items-center justify-between">
                <span className="truncate text-red-300" title={data.label}>{data.label}</span>
            </div>
            <p className="text-xs text-red-400 mt-1">Circular Dependency</p>
        </div>
    );
};
// --- END MODIFICATION ---


const nodeTypes = {
    custom: CustomNode,
    customError: CustomErrorNode,
};

function CodeGraph() {
    const {
        graphNodes, // This is now the *filtered* list
        graphEdges, // This is now the *filtered* list
        onNodesChange,
        onEdgesChange,
        onConnect,
        setSelectedNode,
    } = useStore((state) => ({
        graphNodes: state.graphNodes,
        graphEdges: state.graphEdges,
        onNodesChange: state.onNodesChange,
        onEdgesChange: state.onEdgesChange,
        onConnect: state.onConnect,
        setSelectedNode: state.setSelectedNode,
    }));

    const onNodeClick = useCallback(
        (_: React.MouseEvent, node: Node) => {
            setSelectedNode(node);
        },
        [setSelectedNode]
    );

    return (
        <div style={{ width: '100%', height: '100%' }}>
            <ReactFlow
                nodes={graphNodes}
                edges={graphEdges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                onNodeClick={onNodeClick}
                nodeTypes={nodeTypes}
                fitView
            >
                {/* We REMOVE the default <Controls /> */}
                <MiniMap />
                <Background gap={12} size={1} />
                <GraphControls /> {/* Our custom controls replace the default */}
            </ReactFlow>
        </div>
    );
}

export default CodeGraph;