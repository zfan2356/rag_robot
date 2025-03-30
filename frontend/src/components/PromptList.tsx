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
import { PromptTemplate } from '../api/prompts';

interface PromptListProps {
    prompts: PromptTemplate[];
    onEdit: (id: number) => void;
    onDelete: (id: number) => void;
}

export const PromptList: React.FC<PromptListProps> = ({
    prompts,
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
                            <TableCell>系统提示词</TableCell>
                            <TableCell>创建时间</TableCell>
                            <TableCell>操作</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {prompts.map((prompt) => (
                            <TableRow key={prompt.id}>
                                <TableCell>{prompt.id}</TableCell>
                                <TableCell>{prompt.name}</TableCell>
                                <TableCell>{prompt.description}</TableCell>
                                <TableCell>
                                    {prompt.system_prompt.length > 100
                                        ? `${prompt.system_prompt.substring(0, 100)}...`
                                        : prompt.system_prompt}
                                </TableCell>
                                <TableCell>
                                    {new Date(prompt.created_at).toLocaleString()}
                                </TableCell>
                                <TableCell>
                                    <IconButton
                                        size="small"
                                        onClick={() => onEdit(prompt.id)}
                                        color="primary"
                                    >
                                        <EditIcon />
                                    </IconButton>
                                    <IconButton
                                        size="small"
                                        onClick={() => onDelete(prompt.id)}
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
