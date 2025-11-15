import { create } from 'zustand';
import { Node, Edge, Viewport, applyNodeChanges, applyEdgeChanges, addEdge } from 'reactflow';
import {
    DependencyAnalysis,
    RepositoryNode,
    SSEFileCompleteData,
    Language,
} from './types';
import { fetchGraphAnalysis, getDocumentationStream } from './api-client';
import { getLayoutedElements } from './layout'; // <-- NEW IMPORT

export type AppStatus = 'idle' | 'loading_graph' | 'streaming_docs' | 'error' | 'success';

export interface DocFile {
    path: string;
    summary: string;
    documentation: string;
}

export const initialFilters: Record<Language, boolean> = {
    python: true,
    javascript: true,
    typescript: true,
    unknown: true,
};
export type NodeFilters = typeof initialFilters;

export interface AnalysisState {
    repoUrl: string;
    status: AppStatus;
    error: string | null;

    originalGraphNodes: Node[];
    originalGraphEdges: Edge[];
    graphNodes: Node[];
    graphEdges: Edge[];

    hierarchy: RepositoryNode | null;
    dependencies: DependencyAnalysis | null;

    docFiles: Record<string, DocFile>;
    streamLogs: string[];
    streamProgress: { processed: number; total: number };

    selectedNode: Node | null;
    searchQuery: string;
    nodeFilters: NodeFilters;

    setRepoUrl: (url: string) => void;
    startAnalysis: (url: string) => Promise<void>;
    startStreaming: () => Promise<void>;

    addStreamLog: (log: string) => void;
    setStreamProgress: (progress: { processed: number; total: number }) => void;
    addDocFile: (file: SSEFileCompleteData) => void;
    setError: (error: string) => void;
    setStatus: (status: AppStatus) => void;

    setNodes: (nodes: Node[]) => void;
    setEdges: (edges: Edge[]) => void;
    onNodesChange: (changes: any) => void;
    onEdgesChange: (changes: any) => void;
    onConnect: (connection: any) => void;
    setSelectedNode: (node: Node | null) => void;
    onViewportChange: (viewport: Viewport) => void;

    setSearchQuery: (query: string) => void;
    setNodeFilters: (filters: NodeFilters) => void;
}

export const useStore = create<AnalysisState>((set, get) => ({
    repoUrl: '',
    status: 'idle',
    error: null,

    originalGraphNodes: [],
    originalGraphEdges: [],
    graphNodes: [],
    graphEdges: [],

    hierarchy: null,
    dependencies: null,

    docFiles: {},
    streamLogs: [],
    streamProgress: { processed: 0, total: 0 },

    selectedNode: null,

    searchQuery: '',
    nodeFilters: initialFilters,

    setRepoUrl: (url) => set({ repoUrl: url }),

    startAnalysis: async (url) => {
        set({
            status: 'loading_graph',
            error: null,
            repoUrl: url,
            originalGraphNodes: [],
            originalGraphEdges: [],
            graphNodes: [],
            graphEdges: [],
            hierarchy: null,
            dependencies: null,
            docFiles: {},
            streamLogs: [],
            streamProgress: { processed: 0, total: 0 },
            selectedNode: null,
            searchQuery: '',
            nodeFilters: initialFilters,
        });

        try {
            const data = await fetchGraphAnalysis(url);

            // --- NEW: Apply layout on the frontend ---
            const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
                data.graph_nodes,
                data.graph_edges
            );
            // --- END NEW ---

            set({
                status: 'success',
                // --- MODIFIED: Store layouted data ---
                originalGraphNodes: layoutedNodes,
                originalGraphEdges: layoutedEdges,
                graphNodes: layoutedNodes,
                graphEdges: layoutedEdges,
                // --- END MODIFICATION ---
                hierarchy: data.hierarchy,
                dependencies: data.dependencies,
            });
        } catch (err: any) {
            set({ status: 'error', error: err.message || 'An unknown error occurred' });
        }
    },

    startStreaming: async () => {
        // ... (This function is unchanged) ...
        const { repoUrl } = get();
        if (get().status === 'streaming_docs' || !repoUrl) return;

        set({
            status: 'streaming_docs',
            streamLogs: [],
            docFiles: {},
            streamProgress: { processed: 0, total: 0 },
        });

        try {
            const eventSource = getDocumentationStream(repoUrl);
            eventSource.addEventListener('log', (e) => get().addStreamLog(JSON.parse(e.data)));
            eventSource.addEventListener('parse_complete', (e) => {
                const data = JSON.parse(e.data);
                get().addStreamLog(`Parsing complete. Found ${data.file_count} files.`);
                get().setStreamProgress({ processed: 0, total: data.file_count });
            });
            eventSource.addEventListener('file_complete', (e) => get().addDocFile(JSON.parse(e.data)));
            eventSource.addEventListener('progress', (e) => get().setStreamProgress(JSON.parse(e.data)));
            eventSource.addEventListener('error', (e) => get().addStreamLog(`ERROR: ${JSON.parse(e.data).error}`));
            eventSource.addEventListener('complete', (e) => {
                get().addStreamLog('Documentation generation finished.');
                set({ status: 'success' }); // Back to success state
                eventSource.close();
            });
            eventSource.onerror = (err) => {
                console.error('EventSource failed:', err);
                get().setError('Failed to connect to streaming service.');
                set({ status: 'error' });
                eventSource.close();
            };
        } catch (err: any) {
            set({ status: 'error', error: err.message || 'Failed to start streaming' });
        }
    },

    addStreamLog: (log) =>
        set((state) => ({ streamLogs: [...state.streamLogs, log] })),

    setStreamProgress: (progress) => set({ streamProgress: progress }),

    addDocFile: (file) =>
        set((state) => ({
            docFiles: {
                ...state.docFiles,
                [file.path]: file,
            },
        })),

    setError: (error) => set({ error, status: 'error' }),

    setStatus: (status) => set({ status }),

    // React Flow actions
    setNodes: (nodes) => set({ graphNodes: nodes }),
    setEdges: (edges) => set({ graphEdges: edges }),

    onNodesChange: (changes) => {
        set((state) => ({
            graphNodes: applyNodeChanges(changes, state.graphNodes),
        }));
    },

    onEdgesChange: (changes) => {
        set((state) => ({
            graphEdges: applyEdgeChanges(changes, state.graphEdges),
        }));
    },

    onConnect: (connection) => {
        set((state) => ({
            graphEdges: addEdge(connection, state.graphEdges),
        }));
    },

    setSelectedNode: (node) => set({ selectedNode: node }),

    onViewportChange: (viewport) => { /* console.log('viewport change', viewport); */ },

    setSearchQuery: (query) => {
        set({ searchQuery: query });
        applyGraphFilters();
    },

    setNodeFilters: (filters) => {
        set({ nodeFilters: filters });
        applyGraphFilters();
    },
}));

function applyGraphFilters() {
    const {
        originalGraphNodes,
        originalGraphEdges,
        searchQuery,
        nodeFilters,
        setNodes,
        setEdges
    } = useStore.getState();

    const lowerCaseQuery = searchQuery.toLowerCase();

    const filteredNodes = originalGraphNodes.filter(node => {
        const language = node.data.language as Language;
        return nodeFilters[language] || false;
    });

    const visibleNodeIds = new Set(filteredNodes.map(n => n.id));

    const highlightedNodes = filteredNodes.map(node => {
        const isHighlighted =
            lowerCaseQuery.length > 0 &&
            node.data.label.toLowerCase().includes(lowerCaseQuery);

        return {
            ...node,
            data: {
                ...node.data,
                isHighlighted: isHighlighted,
            },
            style: isHighlighted
                ? { ...node.style,
                    boxShadow: '0 0 10px 3px #fde047',
                    borderColor: '#fde047',
                }
                : node.style,
        };
    });

    const filteredEdges = originalGraphEdges.filter(edge =>
        visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target)
    );

    setNodes(highlightedNodes);
    setEdges(filteredEdges);
}