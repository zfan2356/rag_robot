import { apiClient } from './client';

export interface PromptTemplate {
    id: number;
    name: string;
    description: string;
    system_prompt: string;
    created_at: string;
    updated_at: string;
}

export interface PromptTemplateCreate {
    name: string;
    description: string;
    system_prompt: string;
}

export interface PromptTemplateUpdate {
    name?: string;
    description?: string;
    system_prompt?: string;
}

export const promptApi = {
    // 获取所有提示词模板
    list: async (): Promise<PromptTemplate[]> => {
        const response = await apiClient.get<PromptTemplate[]>('/prompts/list');
        return response.data;
    },

    // 获取指定ID的提示词模板
    get: async (id: number): Promise<PromptTemplate> => {
        const response = await apiClient.get<PromptTemplate>(`/prompts/${id}`);
        return response.data;
    },

    // 通过名称获取提示词模板
    getByName: async (name: string): Promise<PromptTemplate> => {
        const response = await apiClient.get<PromptTemplate>(`/prompts/by_name/${name}`);
        return response.data;
    },

    // 创建提示词模板
    create: async (data: PromptTemplateCreate): Promise<{ id: number; message: string }> => {
        const response = await apiClient.post<{ id: number; message: string }>('/prompts/create', data);
        return response.data;
    },

    // 更新提示词模板
    update: async (id: number, data: PromptTemplateUpdate): Promise<{ message: string }> => {
        const response = await apiClient.put<{ message: string }>(`/prompts/${id}`, data);
        return response.data;
    },

    // 删除提示词模板
    delete: async (id: number): Promise<{ message: string }> => {
        const response = await apiClient.delete<{ message: string }>(`/prompts/${id}`);
        return response.data;
    },
};
