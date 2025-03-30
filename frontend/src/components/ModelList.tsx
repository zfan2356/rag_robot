import React from 'react';
import {
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Typography,
    Box,
} from '@mui/material';
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
            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>ID</TableCell>
                            <TableCell>名称</TableCell>
                            <TableCell>描述</TableCell>
                            <TableCell>创建时间</TableCell>
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
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </Box>
    );
};
