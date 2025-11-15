import { Node, Edge } from 'reactflow';

export type Language = "python" | "javascript" | "typescript" | "unknown";

export interface CodeElement {
    type: "function" | "class" | "method";
    name: string;
    start_line: number;
    end_line: number;
    docstring?: string;
    parameters: string[];
    return_type?: string;
    base_classes: string[];
}

export interface FileNode {
    path: string;
    language: Language;
    size: number;
    elements: CodeElement[];
    imports: string[];
}

export interface FolderNode {
    path: string;
    children: RepositoryNode[];
}

export type RepositoryNode = FileNode | FolderNode;

export interface DependencyInfo {
    path: string;
    imported_by_count: number;
    imports_count: number;
}

export interface CircularDependency {
    nodes: string[];
}

export interface DependencyAnalysis {
    most_imported: DependencyInfo[];
    most_importing: DependencyInfo[];
    isolated_files: string[];
    circular_dependencies: CircularDependency[];
}

export interface GraphAnalysisResponse {
    graph_nodes: Node<any>[];
    graph_edges: Edge<any>[];
    hierarchy: RepositoryNode;
    dependencies: DependencyAnalysis;
}

// For the SSE Stream
export interface SSELogData {
    data: string;
}
export interface SSEParseCompleteData {
    file_count: number;
    files: string[];
}
export interface SSEFileCompleteData {
    path: string;
    summary: string;
    documentation: string;
}
export interface SSEProgressData {
    processed: number;
    total: number;
}
export interface SSEErrorData {
    path?: string;
    error: string;
}
export interface SSECompleteData {
    data: string;
}