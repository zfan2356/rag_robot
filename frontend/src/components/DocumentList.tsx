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
import { DocumentPreview } from '../api/documents';

interface DocumentListProps {
    documents: DocumentPreview[];
    onEdit: (id: number) => void;
    onDelete: (id: number) => void;
}

export const DocumentList: React.FC<DocumentListProps> = ({
    documents,
    onEdit,
    onDelete,
}) => {
    return (
        <Box>
            <Typography variant="h6" gutterBottom>
                文档列表
            </Typography>
            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>ID</TableCell>
                            <TableCell>名称</TableCell>
                            <TableCell>创建时间</TableCell>
                            <TableCell>操作</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {documents.map((doc) => (
                            <TableRow key={doc.id}>
                                <TableCell>{doc.id}</TableCell>
                                <TableCell>{doc.name}</TableCell>
                                <TableCell>
                                    {new Date(doc.created_at).toLocaleString()}
                                </TableCell>
                                <TableCell>
                                    <IconButton
                                        size="small"
                                        onClick={() => onEdit(doc.id)}
                                        color="primary"
                                    >
                                        <EditIcon />
                                    </IconButton>
                                    <IconButton
                                        size="small"
                                        onClick={() => onDelete(doc.id)}
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
