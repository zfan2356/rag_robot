import { apiClient } from './client';

export interface ModelConfig {
    id: number;
    name: string;
    description: string;
    created_at: string;
    updated_at: string;
}

export interface ModelConfigCreate {
    name: string;
    description: string;
}

export interface ModelConfigUpdate {
    name?: string;
    description?: string;
}

export interface ListModelResponse {
    models: ModelConfig[];
}

export const modelApi = {
    // 获取模型列表
    list: async () => {
        try {
            console.log('Fetching models...');
            const response = await apiClient.get<ListModelResponse>('/models/');
            console.log('Models response:', response.data);
            return response.data.models;
        } catch (error) {
            console.error('Failed to fetch models:', error);
            throw error;
        }
    },

    // 获取单个模型
    get: async (name: string) => {
        const response = await apiClient.get<ModelConfig>(`/models/${name}`);
        return response.data;
    },

    // 检查模型是否存在
    check: async (name: string) => {
        const response = await apiClient.get<{ exists: boolean }>(`/models/check/${name}`);
        return response.data.exists;
    },

    // 创建模型
    create: async (model: ModelConfigCreate) => {
        const response = await apiClient.post<ModelConfig>('/models/create', model);
        return response.data;
    },

    // 更新模型
    update: async (id: number, model: ModelConfigUpdate) => {
        const response = await apiClient.put<ModelConfig>(`/models/${id}`, model);
        return response.data;
    },

    // 删除模型
    delete: async (id: number) => {
        const response = await apiClient.delete(`/models/${id}`);
        return response.data;
    },
};
