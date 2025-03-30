import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    Box,
    Button,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Typography,
    Alert,
} from '@mui/material';
import { PromptList } from '../components/PromptList';
import { promptApi, PromptTemplateCreate, PromptTemplateUpdate } from '../api/prompts';

export const Prompts: React.FC = () => {
    const [openDialog, setOpenDialog] = useState(false);
    const [editingPrompt, setEditingPrompt] = useState<number | null>(null);
    const [formData, setFormData] = useState<PromptTemplateCreate>({
        name: '',
        description: '',
        system_prompt: '',
    });

    const queryClient = useQueryClient();

    // 获取提示词模板列表
    const { data: prompts = [], isLoading, error } = useQuery({
        queryKey: ['prompts'],
        queryFn: () => promptApi.list(),
    });

    // 创建提示词模板
    const createMutation = useMutation({
        mutationFn: promptApi.create,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['prompts'] });
            setOpenDialog(false);
            setFormData({ name: '', description: '', system_prompt: '' });
        },
    });

    // 更新提示词模板
    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: number; data: PromptTemplateUpdate }) =>
            promptApi.update(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['prompts'] });
            setOpenDialog(false);
            setEditingPrompt(null);
            setFormData({ name: '', description: '', system_prompt: '' });
        },
    });

    // 删除提示词模板
    const deleteMutation = useMutation({
        mutationFn: promptApi.delete,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['prompts'] });
        },
    });

    const handleOpenDialog = (promptId?: number) => {
        if (promptId) {
            setEditingPrompt(promptId);
            // 获取提示词模板详情
            promptApi.get(promptId).then((prompt) => {
                setFormData({
                    name: prompt.name,
                    description: prompt.description,
                    system_prompt: prompt.system_prompt,
                });
            });
        } else {
            setEditingPrompt(null);
            setFormData({ name: '', description: '', system_prompt: '' });
        }
        setOpenDialog(true);
    };

    const handleCloseDialog = () => {
        setOpenDialog(false);
        setEditingPrompt(null);
        setFormData({ name: '', description: '', system_prompt: '' });
    };

    const handleSubmit = () => {
        if (editingPrompt) {
            updateMutation.mutate({ id: editingPrompt, data: formData });
        } else {
            createMutation.mutate(formData);
        }
    };

    const handleDelete = (id: number) => {
        if (window.confirm('确定要删除这个提示词模板吗？')) {
            deleteMutation.mutate(id);
        }
    };

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
                    加载提示词模板列表失败: {error instanceof Error ? error.message : '未知错误'}
                </Alert>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
            <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="h4">提示词模板管理</Typography>
                <Button
                    variant="contained"
                    color="primary"
                    onClick={() => handleOpenDialog()}
                >
                    新建模板
                </Button>
            </Box>

            <PromptList
                prompts={prompts}
                onEdit={handleOpenDialog}
                onDelete={handleDelete}
            />

            <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
                <DialogTitle>
                    {editingPrompt ? '编辑提示词模板' : '新建提示词模板'}
                </DialogTitle>
                <DialogContent>
                    <Box sx={{ pt: 2 }}>
                        <TextField
                            fullWidth
                            label="模板名称"
                            value={formData.name}
                            onChange={(e) =>
                                setFormData({ ...formData, name: e.target.value })
                            }
                            margin="normal"
                        />
                        <TextField
                            fullWidth
                            label="模板描述"
                            value={formData.description}
                            onChange={(e) =>
                                setFormData({ ...formData, description: e.target.value })
                            }
                            margin="normal"
                            multiline
                            rows={2}
                        />
                        <TextField
                            fullWidth
                            label="系统提示词"
                            value={formData.system_prompt}
                            onChange={(e) =>
                                setFormData({ ...formData, system_prompt: e.target.value })
                            }
                            margin="normal"
                            multiline
                            rows={6}
                        />
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseDialog}>取消</Button>
                    <Button
                        onClick={handleSubmit}
                        variant="contained"
                        color="primary"
                        disabled={!formData.name || !formData.description || !formData.system_prompt}
                    >
                        确定
                    </Button>
                </DialogActions>
            </Dialog>

            {(createMutation.isError || updateMutation.isError || deleteMutation.isError) && (
                <Alert severity="error" sx={{ mt: 2 }}>
                    操作失败，请重试
                </Alert>
            )}
        </Box>
    );
};
