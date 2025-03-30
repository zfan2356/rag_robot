import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
    Box,
    Typography,
    Alert,
} from '@mui/material';
import { ModelList } from '../components/ModelList';
import { modelApi } from '../api/models';

export const Models: React.FC = () => {
    // 获取模型列表
    const { data: models = [], isLoading, error } = useQuery({
        queryKey: ['models'],
        queryFn: () => modelApi.list(),
    });

    if (isLoading) {
        return (
            <Box sx={{ p: 3, display: 'flex', justifyContent: 'center' }}>
                <Typography>加载中...</Typography>
            </Box>
        );
    }

    if (error) {
        return (
            <Box sx={{ p: 3 }}>
                <Alert severity="error">
                    加载模型列表失败: {error instanceof Error ? error.message : '未知错误'}
                </Alert>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
            <Box sx={{ mb: 3 }}>
                <Typography variant="h4">模型列表</Typography>
            </Box>

            <ModelList
                models={models}
                onEdit={() => { }}
                onDelete={() => { }}
            />
        </Box>
    );
};
