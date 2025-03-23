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
import { ModelList } from '../components/ModelList';
import { modelApi, ModelConfigCreate, ModelConfigUpdate } from '../api/models';

export const Models: React.FC = () => {
    const [openDialog, setOpenDialog] = useState(false);
    const [editingModel, setEditingModel] = useState<number | null>(null);
    const [formData, setFormData] = useState<ModelConfigCreate>({
        name: '',
        description: '',
    });

    const queryClient = useQueryClient();

    // 获取模型列表
    const { data: models = [], isLoading, error } = useQuery({
        queryKey: ['models'],
        queryFn: () => modelApi.list(),
    });

    // 创建模型
    const createMutation = useMutation({
        mutationFn: modelApi.create,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['models'] });
            setOpenDialog(false);
            setFormData({ name: '', description: '' });
        },
    });

    // 更新模型
    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: number; data: ModelConfigUpdate }) =>
            modelApi.update(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['models'] });
            setOpenDialog(false);
            setEditingModel(null);
            setFormData({ name: '', description: '' });
        },
    });

    // 删除模型
    const deleteMutation = useMutation({
        mutationFn: modelApi.delete,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['models'] });
        },
    });

    const handleOpenDialog = (modelId?: number) => {
        if (modelId) {
            setEditingModel(modelId);
            // 获取模型详情
            modelApi.get(modelId).then((model) => {
                setFormData({ name: model.name, description: model.description });
            });
        } else {
            setEditingModel(null);
            setFormData({ name: '', description: '' });
        }
        setOpenDialog(true);
    };

    const handleCloseDialog = () => {
        setOpenDialog(false);
        setEditingModel(null);
        setFormData({ name: '', description: '' });
    };

    const handleSubmit = () => {
        if (editingModel) {
            updateMutation.mutate({ id: editingModel, data: formData });
        } else {
            createMutation.mutate(formData);
        }
    };

    const handleDelete = (id: number) => {
        if (window.confirm('确定要删除这个模型吗？')) {
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
                    加载模型列表失败: {error instanceof Error ? error.message : '未知错误'}
                </Alert>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
            <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="h4">模型管理</Typography>
                <Button
                    variant="contained"
                    color="primary"
                    onClick={() => handleOpenDialog()}
                >
                    新建模型
                </Button>
            </Box>

            <ModelList
                models={models}
                onEdit={handleOpenDialog}
                onDelete={handleDelete}
            />

            <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
                <DialogTitle>
                    {editingModel ? '编辑模型' : '新建模型'}
                </DialogTitle>
                <DialogContent>
                    <Box sx={{ pt: 2 }}>
                        <TextField
                            fullWidth
                            label="模型名称"
                            value={formData.name}
                            onChange={(e) =>
                                setFormData({ ...formData, name: e.target.value })
                            }
                            margin="normal"
                        />
                        <TextField
                            fullWidth
                            label="模型描述"
                            value={formData.description}
                            onChange={(e) =>
                                setFormData({ ...formData, description: e.target.value })
                            }
                            margin="normal"
                            multiline
                            rows={4}
                        />
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseDialog}>取消</Button>
                    <Button
                        onClick={handleSubmit}
                        variant="contained"
                        color="primary"
                        disabled={!formData.name || !formData.description}
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
