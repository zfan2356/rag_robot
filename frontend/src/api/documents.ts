import { apiClient } from './client';

export interface Document {
    id: number;
    title: string;
    doc: string;
    created_at: string;
    updated_at: string;
}

export interface DocumentPreview {
    id: number;
    title: string;
    doc_preview: string;
    created_at: string;
    updated_at: string;
}

export interface DocumentCreate {
    title: string;
    doc: string;
}

export interface DocumentUpdate {
    title?: string;
    doc?: string;
}

export const documentApi = {
    // 获取文档列表
    list: async (skip: number = 0, limit: number = 100) => {
        try {
            console.log('Fetching documents with:', { skip, limit });
            const response = await apiClient.get<DocumentPreview[]>('/documents/list', {
                params: { skip, limit },
            });
            console.log('Documents response:', response.data);
            return response.data;
        } catch (error) {
            console.error('Failed to fetch documents:', error);
            throw error;
        }
    },

    // 获取文档总数
    count: async () => {
        const response = await apiClient.get<{ total: number }>('/documents/count');
        return response.data.total;
    },

    // 搜索文档
    search: async (keyword: string) => {
        const response = await apiClient.get<DocumentPreview[]>('/documents/search', {
            params: { keyword },
        });
        return response.data;
    },

    // 获取单个文档
    get: async (id: number) => {
        const response = await apiClient.get<Document>(`/documents/${id}`);
        return response.data;
    },

    // 创建文档
    create: async (document: DocumentCreate) => {
        const response = await apiClient.post<Document>('/documents/create', document);
        return response.data;
    },

    // 更新文档
    update: async (id: number, document: DocumentUpdate) => {
        const response = await apiClient.put<Document>(`/documents/${id}`, document);
        return response.data;
    },

    // 删除文档
    delete: async (id: number) => {
        const response = await apiClient.delete(`/documents/${id}`);
        return response.data;
    },
};
