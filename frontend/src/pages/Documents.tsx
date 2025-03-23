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
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
} from '@mui/material';
import { documentApi, DocumentCreate, DocumentUpdate } from '../api/documents';

export const Documents: React.FC = () => {
    const [openDialog, setOpenDialog] = useState(false);
    const [editingDoc, setEditingDoc] = useState<number | null>(null);
    const [formData, setFormData] = useState<DocumentCreate>({
        title: '',
        doc: '',
    });

    const queryClient = useQueryClient();

    // 获取文档列表
    const { data: documents = [], isLoading, error } = useQuery({
        queryKey: ['documents'],
        queryFn: () => documentApi.list(),
        staleTime: 1000 * 60, // 1分钟内不重新请求
        retry: 2, // 失败时重试2次
    });

    // 创建文档
    const createMutation = useMutation({
        mutationFn: documentApi.create,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['documents'] });
            setOpenDialog(false);
            setFormData({ title: '', doc: '' });
        },
    });

    // 更新文档
    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: number; data: DocumentUpdate }) =>
            documentApi.update(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['documents'] });
            setOpenDialog(false);
            setEditingDoc(null);
            setFormData({ title: '', doc: '' });
        },
    });

    // 删除文档
    const deleteMutation = useMutation({
        mutationFn: documentApi.delete,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['documents'] });
        },
    });

    const handleOpenDialog = (docId?: number) => {
        if (docId) {
            setEditingDoc(docId);
            // 获取文档详情
            documentApi.get(docId).then((doc) => {
                setFormData({ title: doc.title, doc: doc.doc });
            });
        } else {
            setEditingDoc(null);
            setFormData({ title: '', doc: '' });
        }
        setOpenDialog(true);
    };

    const handleCloseDialog = () => {
        setOpenDialog(false);
        setEditingDoc(null);
        setFormData({ title: '', doc: '' });
    };

    const handleSubmit = () => {
        if (editingDoc) {
            updateMutation.mutate({ id: editingDoc, data: formData });
        } else {
            createMutation.mutate(formData);
        }
    };

    const handleDelete = (id: number) => {
        if (window.confirm('确定要删除这个文档吗？')) {
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
                    加载文档列表失败: {error instanceof Error ? error.message : '未知错误'}
                </Alert>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
            <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="h4">文档管理</Typography>
                <Button
                    variant="contained"
                    color="primary"
                    onClick={() => handleOpenDialog()}
                >
                    新建文档
                </Button>
            </Box>

            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>ID</TableCell>
                            <TableCell>标题</TableCell>
                            <TableCell>预览</TableCell>
                            <TableCell>创建时间</TableCell>
                            <TableCell>更新时间</TableCell>
                            <TableCell>操作</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {documents?.map((doc) => (
                            <TableRow key={doc.id}>
                                <TableCell>{doc.id}</TableCell>
                                <TableCell>{doc.title}</TableCell>
                                <TableCell>{doc.doc_preview}</TableCell>
                                <TableCell>{new Date(doc.created_at).toLocaleString()}</TableCell>
                                <TableCell>{new Date(doc.updated_at).toLocaleString()}</TableCell>
                                <TableCell>
                                    <Button
                                        size="small"
                                        onClick={() => handleOpenDialog(doc.id)}
                                    >
                                        编辑
                                    </Button>
                                    <Button
                                        size="small"
                                        color="error"
                                        onClick={() => handleDelete(doc.id)}
                                    >
                                        删除
                                    </Button>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>

            <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
                <DialogTitle>
                    {editingDoc ? '编辑文档' : '新建文档'}
                </DialogTitle>
                <DialogContent>
                    <Box sx={{ pt: 2 }}>
                        <TextField
                            fullWidth
                            label="文档标题"
                            value={formData.title}
                            onChange={(e) =>
                                setFormData({ ...formData, title: e.target.value })
                            }
                            margin="normal"
                        />
                        <TextField
                            fullWidth
                            label="文档内容"
                            value={formData.doc}
                            onChange={(e) =>
                                setFormData({ ...formData, doc: e.target.value })
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
                        disabled={!formData.title || !formData.doc}
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
