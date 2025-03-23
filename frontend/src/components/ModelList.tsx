import React from 'react';
import {
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    IconButton,
    Typography,
    Box,
} from '@mui/material';
import { Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { ModelConfig } from '../api/models';

interface ModelListProps {
    models: ModelConfig[];
    onEdit: (id: number) => void;
    onDelete: (id: number) => void;
}

export const ModelList: React.FC<ModelListProps> = ({
    models,
    onEdit,
    onDelete,
}) => {
    return (
        <Box>
            <Typography variant="h6" gutterBottom>
                模型列表
            </Typography>
            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>ID</TableCell>
                            <TableCell>名称</TableCell>
                            <TableCell>描述</TableCell>
                            <TableCell>创建时间</TableCell>
                            <TableCell>操作</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {models.map((model) => (
                            <TableRow key={model.id}>
                                <TableCell>{model.id}</TableCell>
                                <TableCell>{model.name}</TableCell>
                                <TableCell>{model.description}</TableCell>
                                <TableCell>
                                    {new Date(model.created_at).toLocaleString()}
                                </TableCell>
                                <TableCell>
                                    <IconButton
                                        size="small"
                                        onClick={() => onEdit(model.id)}
                                        color="primary"
                                    >
                                        <EditIcon />
                                    </IconButton>
                                    <IconButton
                                        size="small"
                                        onClick={() => onDelete(model.id)}
                                        color="error"
                                    >
                                        <DeleteIcon />
                                    </IconButton>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </Box>
    );
};
